# BeatCue developers' guide

This guide is for contributors implementing BeatCue. It summarizes the
architecture, package boundaries, tooling, and verification expectations that
turn the [technical design](beatcue-technical-design.md) and
[roadmap](roadmap.md) into code.

Read `AGENTS.md` before changing the repository. It defines the required local
workflow, quality gates, and documentation standards.

## Current repository state

The repository currently contains:

- the Python package skeleton in `beatcue/`;
- a smoke-check package API, `beatcue.hello()`;
- the technical design in `docs/beatcue-technical-design.md`;
- the development roadmap in `docs/roadmap.md`;
- this guide and the users' guide.

The planned video-analysis API and CLI are not implemented yet. Do not document
planned commands as available until the implementation lands.

The v1 implementation boundary is deterministic cue extraction for
single-scene or single-shot videos. Semantic annotation, object tracking, OTIO
enrichment, remote model execution, GPU scheduling, and advanced segmentation
are post-v1 unless a later design update changes the boundary.

## Architectural rules

BeatCue uses hexagonal architecture. Dependencies point inward:

```plaintext
CLI and library adapters -> application services -> domain model and ports
outbound adapters        -> domain-owned ports
```

The main rule is simple: domain code must not import infrastructure. Domain
modules should not import Cyclopts, Rich, OpenCV, librosa, Transformers,
Cuprum, CmdMox, filesystem adapters, or CLI modules.

Planned package boundaries:

| Package                     | Responsibility                                                                                                                     |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `beatcue.domain`            | Pure domain values, cue types, feature summaries, invariants, and port protocols.                                                  |
| `beatcue.application`       | Use cases that orchestrate domain services through injected ports.                                                                 |
| `beatcue.adapters.inbound`  | Driving adapters such as the Cyclopts CLI and library facade.                                                                      |
| `beatcue.adapters.outbound` | Driven adapters for media probing, frame sampling, audio, vision, model inference, writers, jobs, profiles, and command execution. |
| `beatcue.config`            | Composition root that binds configuration to concrete adapters.                                                                    |

_Table 1: Planned package responsibilities._

Every external dependency enters through an adapter. Application services
receive adapters through constructor injection or explicit composition
functions. Avoid module-level singletons for services, command runners, model
instances, or stores.

## Domain and application APIs

The domain owns the canonical value objects:

- media metadata;
- time ranges;
- feature summaries;
- cue kinds;
- cues;
- object observations;
- diagnostics;
- provenance.

Domain values should be immutable where practical. Validate invariants at the
boundary:

- `0 <= start_seconds <= end_seconds`;
- confidence values are finite and within `[0.0, 1.0]`;
- cue IDs are stable for the same input, configuration, and cue order;
- semantic annotations cannot create timing cues without deterministic timing
  evidence.

Application services own workflows such as `AnalyseVideo`, profile management,
job recovery, and `agent-context` generation. They coordinate ports but should
not know whether a frame came from OpenCV, a caption came from Transformers, or
an external command ran through a particular binary path.

## Ports and adapters

Define port protocols in the domain using domain language. Keep each port
minimal and cohesive.

Required driven ports from the design include:

- `MediaProbe`;
- `FrameSampler`;
- `AudioExtractor`;
- `AudioFeatureExtractor`;
- `SceneDetector`;
- `MotionExtractor`;
- `ObjectTracker`;
- `SemanticAnnotator`;
- `CueWriter`;
- `JobLedger`;
- `ProfileStore`;
- `CommandRunner`.

Adapters implement these protocols and convert infrastructure types into domain
types before returning. Do not leak NumPy arrays, OpenCV frames, Pydantic
models, Cuprum result types, or Transformers objects into domain APIs unless a
design update explicitly changes that contract.

## Subprocess tooling

All external commands must run through the Cuprum-backed command adapter. Do
not call `subprocess.run`, `os.system`, or shell strings directly from BeatCue
code.

The command catalogue should start with:

- `ffprobe`;
- `ffmpeg`;
- optional helper commands required by documented adapters.

The command adapter records argument vectors, working directory, timeout, exit
code, and captured output when enabled. It must record environment overlay keys
without recording secret values.

Tests for command adapters use CmdMox. Use CmdMox to verify exact command
vectors and to simulate missing binaries, malformed JSON, non-zero exits, and
no-audio media.

## CLI implementation requirements

Cyclopts owns the CLI specification. Keep CLI argument type annotations
available at runtime because command registration resolves type hints.

The root CLI must support:

- `--profile NAME`;
- `--config PATH`;
- `--json`;
- `--no-input`;
- `--plain`;
- `--verbose`.

Planned commands:

- `analyse VIDEO`;
- `inspect VIDEO`;
- `agent-context`;
- `jobs list`, `jobs get`, and `jobs prune`;
- `profile list`, `profile show`, `profile save`, and `profile delete`;
- `feedback add`, `feedback list`, and `feedback send`.

CLI rules:

- Do not prompt unless `--interactive` is explicitly set.
- Emit data to standard output.
- Emit diagnostics, progress, and Rich human output to standard error.
- Support `--json` on every data-returning command.
- Require `--force` for destructive overwrite or deletion behaviour.
- Bound list outputs and expose pagination or limits.
- Enumerate valid values in enum validation errors.
- Keep machine and LLM-facing output clean ASCII unless the selected writer
  explicitly permits source Unicode.

Rich belongs only in the human output adapter. Domain, application, and writer
contracts should not depend on Rich renderables.

## Configuration

Configuration precedence is:

```plaintext
explicit CLI flag > environment variable > profile > config file > default
```

The composition root is responsible for merging configuration and constructing
immutable request objects. Profiles may store reusable analysis settings, model
names, output preferences, and thresholds. They must not store API keys or
other secrets.

Use `BEATCUE_HOME` in tests when profile or job storage needs an isolated
directory.

## Output writers

All writers consume the canonical analysis result. Do not let one writer become
the source of truth for another writer.

Writer expectations:

- BeatCue JSON is the lossless output and should round-trip through the
  selected `msgspec.Struct` schema. ADR 003 records this decision; implement
  schema structs at the serialization boundary and map from immutable domain
  values rather than importing writer types into the domain.
- WebVTT contains compact metadata cues with ASCII JSON payloads by default.
- Post-v1 OTIO output should use the OpenTimelineIO library rather than
  hand-written OTIO JSON.
- Human summaries use Rich and do not affect JSON, WebVTT, or OTIO output.

Syrupy snapshots should cover externally visible output contracts. When a
snapshot changes, the pull request should explain whether the change is a
schema update, a formatting update, or a behaviour change.

## Testing strategy

Use the test tool that matches the boundary:

| Boundary                  | Tooling                            |
| ------------------------- | ---------------------------------- |
| Domain invariants         | pytest and Hypothesis              |
| Application orchestration | pytest with injected fake ports    |
| CLI workflows             | pytest-bdd and snapshot assertions |
| Writer contracts          | syrupy snapshots                   |
| External commands         | CmdMox                             |
| Adapter smoke tests       | small generated media fixtures     |

_Table 2: Boundary-specific test tooling._

Do not create standalone roadmap tasks only to add ordinary unit or behavioural
tests. Tests are part of the implementation task. Dedicated end-to-end and
combinatorial suites are appropriate when they cover flag interactions,
multi-adapter workflows, or cross-format contracts.

High-value property-based checks include:

- timestamp normalization;
- cue fusion over sorted, unsorted, overlapping, and empty lists;
- confidence normalization;
- WebVTT millisecond rounding;
- configuration precedence;
- semantic annotation rejection when deterministic cue evidence is missing.

## Quality gates

Prefer Makefile targets over direct tool calls. For Markdown-only changes, run:

```bash
make markdownlint
make nixie
```

For Python changes, run the full relevant gate set:

```bash
make check-fmt
make lint
make typecheck
make test
```

Use `tee` logs under `/tmp` for gates so long output remains reviewable. Do not
run tests, linters, or format checks in parallel.

## Documentation updates

Update documentation in the same change set when implementation changes user
behaviour, public APIs, configuration, output formats, architecture boundaries,
or tooling. Relevant files:

- `docs/users-guide.md` for user workflows and CLI/library usage;
- `docs/developers-guide.md` for architecture, contribution, and tooling
  guidance;
- `docs/beatcue-technical-design.md` for design-level decisions;
- `docs/roadmap.md` for planned delivery sequence and completion status;
- `README.md` for high-level orientation and links.

Follow `docs/documentation-style-guide.md`: British English with Oxford
spelling, sentence-case headings, wrapped prose, language identifiers on fenced
code blocks, and Mermaid validation where diagrams are present.
