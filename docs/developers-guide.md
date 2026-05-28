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

The v1 implementation boundary is deterministic cue extraction for single-scene
or single-shot videos. Semantic annotation, object tracking, OTIO enrichment,
remote model execution, graphics processing unit (GPU) scheduling, and advanced
segmentation are post-v1 unless a later design update changes the boundary. ADR
005 records the selected object-tracking boundary for that later work. ADR 006
records the v1 local-only model and privacy policy: remote model execution is
out of scope until a separate privacy and credentials design is accepted.

## Architectural rules

BeatCue uses hexagonal architecture. Dependencies point inward:

```plaintext
CLI and library adapters -> application services -> domain model and ports
outbound adapters        -> domain-owned ports
```

The main rule is simple: domain code must not import infrastructure. Domain
modules should not import Cyclopts, Rich, OpenCV, librosa, Transformers,
Cuprum, CmdMox, filesystem adapters, or CLI modules.

Production package boundaries:

- `beatcue.domain`: Pure domain values, cue types, feature summaries,
  invariants, and port protocols.
- `beatcue.application`: Use cases that orchestrate domain services through
  injected ports.
- `beatcue.adapters.inbound`: Driving adapters such as the Cyclopts CLI and
  library facade.
- `beatcue.adapters.outbound`: Driven adapters for media probing, frame
  sampling, audio, vision, model inference, writers, jobs, profiles, and
  command execution.
- `beatcue.config`: Composition root that binds configuration to concrete
  adapters.

Every external dependency enters through an adapter. Application services
receive adapters through constructor injection or explicit composition
functions. Avoid module-level singletons for services, command runners, model
instances, or stores.

BeatCue enforces these import-direction rules with
[Hecate](https://github.com/leynos/hecate), pinned in the development
dependencies and configured by `[tool.hecate]` in `pyproject.toml`. Run the
gate directly with:

```bash
make check-architecture
```

The ordinary lint target also runs Hecate after Ruff and Pylint:

```bash
make lint
```

Hecate scans the current `beatcue/` package and reports `ARCH001` when a module
imports a forbidden architecture group. The policy groups are ordered: specific
prefixes such as `beatcue.adapters.outbound` must appear before broader
prefixes such as `beatcue.adapters`. Keep documented exceptions as
`[[tool.hecate.ignore_imports]]` entries with a non-empty reason; do not use
ignores to mask real boundary violations.

The production boundary packages exist only where they express the
architecture. Keep their `__init__.py` files free of cross-layer imports. Add
behaviour modules only when the corresponding roadmap work lands. BeatCue
tests should cover BeatCue-specific policy examples and leave parser,
configuration, and re-export internals to Hecate's own test suite.

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

`ObjectTracker` is a domain-owned post-v1 port. Keep tracker protocols and
track lifecycle values in the domain. Keep detector adapters, tracker adapters,
model clients, OpenCV objects, Transformers objects, Torch tensors, Pillow
images, and remote service clients outside the domain. The first tracker should
use deterministic centroid association over plain detector observations, so
fixtures can prove stable track IDs, entry and exit edges, missing detections,
and confidence handling without model inference.

Future model adapters must follow ADR 006. Backends advertise locality and
capabilities explicitly through the configured capability set; do not infer
remote support from an installed package, model name, or adapter brand. A
requested remote backend that is not configured must fail before inference with
a capability error that names the backend and points to the local-only v1
policy. Adapters must not silently fall back from local execution to remote
execution, and local adapters should use explicit offline or local-file
controls where their underlying libraries provide them.

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
names, output preferences, and thresholds. They must not store API keys, bearer
tokens, session cookies, OAuth tokens, refresh tokens, or other remote-service
credentials. Remote backend support requires the future roadmap item 6.1
privacy and credentials work before implementation.

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
- object-track lifecycle invariants, including persistence thresholds, empty
  observation lists, missing detections, and non-finite confidence rejection;
- WebVTT millisecond rounding;
- configuration precedence;
- semantic annotation rejection when deterministic cue evidence is missing.

Use Vidai Mock only for behavioural tests that exercise inference-service
adapters. Pure centroid-association tests should use deterministic observations
and in-memory fakes rather than model simulation.

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

### Linting architecture

BeatCue uses the linting architecture recorded in
[ADR 004](adr-004-two-tier-python-linting.md). The lint gate is deliberately
two-tier:

1. Ruff runs first from the project virtual environment.
2. Pylint runs second through the pinned
   [`pylint-pypy-shim`](https://github.com/leynos/pylint-pypy-shim) tool under
   PyPy.

Ruff is the fast, broad gate for style, import hygiene, annotation discipline,
bug patterns, performance hints, docstring policy, and Ruff's own Pylint-style
rules. Pylint is the slower second tier for selected checks that Ruff does not
cover with the same semantics, especially logging format issues, pattern
matching hazards, simplification opportunities, mutation during iteration,
resource handling, and structural complexity limits.

Run both tiers with:

```bash
make lint
```

The `lint` target depends on the `.deps` stamp. That stamp refreshes the
`.venv` from `pyproject.toml` only when the environment or dependency
configuration is stale, then runs:

```bash
$(UV_ENV) $(UV) run ruff check
$(PYLINT) $(PYLINT_TARGETS)
```

Use the Makefile target rather than invoking `ruff` or `pylint` directly. This
keeps the selected interpreter, cache directories, shim revision, and target
set consistent between local development and review.

### Lint Makefile variables

The lint target is configured by these Makefile variables:

- `UV`: defaults to `uv`. This selects the `uv` executable used for
  virtual-environment and tool execution, and the Makefile fails early with a
  clear error if it is unavailable.
- `UV_ENV`: defaults to `UV_CACHE_DIR=.uv-cache UV_TOOL_DIR=.uv-tools`. This
  keeps `uv` cache and tool state local to the checkout.
- `.deps`: records that `uv sync --group dev` has run for the current
  `pyproject.toml` and `.venv`, avoiding an unconditional sync on every
  formatting or lint invocation.
- `PYLINT_PYTHON`: defaults to `pypy`. This selects the interpreter used for
  the shimmed Pylint run.
- `PYLINT_TARGETS`: defaults to `beatcue tests`. This defines the directories
  linted by the Pylint tier.
- `PYLINT_PYPY_SHIM_REF`: defaults to
  `726d09f968b4d729ee4b29c71fc732e744854f3b`. This pins the shim repository
  revision for reproducible Pylint behaviour.
- `PYLINT_PYPY_SHIM`: defaults to the pinned
  `git+https://github.com/leynos/pylint-pypy-shim.git` source assembled from
  `PYLINT_PYPY_SHIM_REF`. This defines the install source used by `uv tool run`.
- `PYLINT`: assembles the complete `uv tool run --python ... pylint-pypy`
  command used by `make lint`.

Override these variables only when diagnosing the lint toolchain itself. Pull
requests should not depend on local overrides to pass.

### Episodic lint policy

BeatCue imports the Python lint policy from
[Episodic](https://github.com/leynos/episodic) so related df12 Python projects
share one linting posture. The imported policy includes:

- Ruff preview mode and `target-version = "py314"`;
- a broad Ruff `select` list covering Pyflakes, pycodestyle, import sorting,
  pyupgrade, comprehensions, future annotations, tidy imports, type-checking
  imports, pathlib use, TODO hygiene, security checks, datetime handling,
  boolean traps, naming, logging, pytest, returns, performance, docstrings,
  annotations, McCabe complexity, and selected Ruff rules;
- Ruff banned `typing.*` APIs that steer code towards built-in generics,
  `collections.abc`, `contextlib`, `collections`, and `re` runtime types;
- NumPy-style docstrings through Ruff's pydocstyle integration;
- focused Pylint design thresholds and message selection.

When the Episodic policy changes, update BeatCue intentionally rather than
copying blindly. The pull request should explain whether the change tightens
the shared policy, adapts BeatCue to a local constraint, or deliberately
diverges from Episodic.

### `pyproject.toml` lint configuration

The active lint configuration lives in `pyproject.toml`:

- `[tool.ruff]` sets line length, preview mode, and Python target version.
- `[tool.ruff.lint]` defines the selected Ruff rule families and shared
  ignores.
- `[tool.ruff.lint.per-file-ignores]` relaxes assertion, parameter-count,
  magic-value, and method-shape rules for test modules where fixtures and
  behavioural tests need different trade-offs.
- `[tool.ruff.lint.flake8-import-conventions]` and
  `[tool.ruff.lint.flake8-import-conventions.aliases]` require canonical module
  imports and aliases.
- `[tool.ruff.lint.flake8-tidy-imports.banned-api]` rejects deprecated
  `typing.*` spellings in favour of runtime-safe alternatives.
- `[tool.ruff.lint.pydocstyle]`, `[tool.ruff.lint.mccabe]`, and
  `[tool.ruff.lint.pylint]` set docstring style and local complexity limits.
- `[tool.pylint.main]`, `[tool.pylint.design]`, and
  `[tool.pylint."messages control"]` keep Pylint focused on the selected
  second-tier checks. The enabled Pylint messages are grouped by purpose so
  logging, pattern matching, simplification, resource, hygiene, mutation, and
  complexity checks can be reviewed independently.

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
