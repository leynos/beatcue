# BeatCue roadmap

This roadmap translates [BeatCue technical design](beatcue-technical-design.md)
into an outcome-oriented delivery sequence. It does not promise dates. Each
phase carries a testable idea at the GIST level. The steps underneath that
phase validate or falsify the idea, answer sequencing questions, and deliver
usable functionality instead of isolated layers.

The roadmap cites the design document sections that define each task. Future
architectural decision records (ADRs) should live in `docs/` and should be
linked from the tasks that create or depend on them.

## 1. Foundational contracts and build spine

Idea: if BeatCue settles its domain contracts, dependency boundaries, and
quality gates before feature work starts, later cue-extraction slices can
converge on one coherent package instead of reworking interfaces around every
adapter.

This phase establishes the promises that later phases depend on: the hexagonal
boundary, public package shape, selected schema technology, command catalogue,
real-I/O walking skeleton, and test fixture strategy. It should leave a small
but enforceable skeleton that can reject architectural drift early.

### 1.1. Ratify the v1 architecture and deferred decisions

This step answers which decisions belong in v1 and which remain explicitly
deferred. Its outcome informs package layout, dependency selection, and the
first public API boundary. See beatcue-technical-design.md §§2-8, §13.1, and
§21.

- [x] 1.1.1. Record the v1 schema decision for BeatCue JSON.
  - Ratify `msgspec.Struct` as the selected v1 schema technology in an ADR if
    the project still wants a separate decision record.
  - See beatcue-technical-design.md §§7, 13.1, and 17.
  - Decision: ADR 003 ratifies `msgspec.Struct` as the BeatCue JSON v1 schema
    technology.
  - Success: the ADR or design signpost explains why `msgspec` is suitable for
    library callers, CLI output, round-trip validation, and stable snapshots.
- [ ] 1.1.2. Record the v1 object-tracking boundary.
  - Requires 1.1.1.
  - Decide whether v1 uses a centroid tracker, Florence-2-only detections, or a
    pluggable tracker port with a simple default.
  - See beatcue-technical-design.md §§8, 11, 12, and 21.
  - Success: later object-entry tasks can implement one selected boundary
    without reopening the model-adapter decision.
- [ ] 1.1.3. Record the local-only model and privacy policy for v1.
  - Requires 1.1.1.
  - Confirm that remote model execution remains out of scope until a separate
    privacy and credentials design exists.
  - See beatcue-technical-design.md §§12, 19, and 21.
  - Success: model adapters fail clearly when a requested remote backend is not
    part of the configured capability set.

### 1.2. Establish the package skeleton and architecture fitness checks

This step answers whether the repository can enforce the intended dependency
direction during normal development. The outcome informs every implementation
task after this phase. See beatcue-technical-design.md §§5-8 and §17.

- [ ] 1.2.1. Create the `domain`, `application`, `adapters`, and `config`
  package skeleton.
  - Requires 1.1.1.
  - Include placeholder modules only where they express a real boundary.
  - See beatcue-technical-design.md §§5-8.
  - Success: imports reflect the design's inward dependency rule before any
    infrastructure adapters land.
- [ ] 1.2.2. Add a CI fitness function for forbidden imports.
  - Requires 1.2.1.
  - Reject domain imports from adapters, Cyclopts, Rich, OpenCV, librosa,
    Transformers, Cuprum, and CmdMox.
  - See beatcue-technical-design.md §5.
  - Success: a deliberate adapter import in `beatcue.domain` fails the gate.
- [ ] 1.2.3. Wire the development dependencies required by the design.
  - Requires 1.2.1.
  - Add runtime or optional dependency groups for Cyclopts, Rich, Cuprum,
    OpenTimelineIO, OpenCV, librosa, PySceneDetect, Transformers, and related
    optional model packages.
  - Add development dependencies for pytest-bdd, syrupy, Hypothesis, and
    CmdMox.
  - See beatcue-technical-design.md §§14, 16, and 17.
  - Success: `make all` installs the package and can discover the empty unit
    and behavioural test suites.

### 1.3. Prove real I/O through a walking skeleton

This step answers whether the intended architecture can touch a real video
file and write a real cue sheet before deeper feature extraction work begins.
It is a narrow proof, not the final analysis pipeline. See
beatcue-technical-design.md §§5, 8, 9, 13.2, and 16, and
beatcue-logisphere-design-stage-review.md §4 scenario A and §8 recommended
step 5.

- [ ] 1.3.1. Implement the real-I/O walking skeleton.
  - Requires 1.2.3.
  - Probe a tiny media fixture through the Cuprum-backed `ffprobe` port, sample
    one frame through the frame-sampler port, create one synthetic cue in the
    application layer, and write one WebVTT file through the writer port.
  - See beatcue-technical-design.md §§5, 8, 9, 13.2, and 16.
  - Success: one command or test proves
    `ffprobe` -> one sampled frame -> one-cue WebVTT through the
    domain/application/adapter boundaries.

### 1.4. Build the shared fixture and contract-test spine

This step answers how BeatCue will keep outputs stable while the extraction
pipeline changes. Its outcome informs writer, CLI, and adapter work. See
beatcue-technical-design.md §§7, 13, 16, and 17.

- [ ] 1.4.1. Add canonical in-memory analysis fixtures.
  - Requires 1.2.3.
  - Cover cuts, beats, ease cues, action arcs, object observations, semantic
    annotations, diagnostics, and provenance.
  - See beatcue-technical-design.md §§7, 10-13, and 17.
  - Success: fixtures can serialize through the selected schema without
    non-deterministic cue IDs.
- [ ] 1.4.2. Add property generators for timing and confidence invariants.
  - Requires 1.4.1.
  - Generate time ranges, cue windows, merge tolerances, confidence values, and
    configuration precedence inputs.
  - See beatcue-technical-design.md §17.
  - Success: Hypothesis can falsify an intentionally invalid time range or
    confidence normalization rule.
- [ ] 1.4.3. Add CmdMox fixtures for `ffprobe` and `ffmpeg`.
  - Requires 1.2.3.
  - Cover success, missing binary, malformed JSON, no-audio media, and non-zero
    exit status.
  - See beatcue-technical-design.md §§16-18.
  - Success: adapter tests verify the exact command vector without invoking
    real external commands.

## 2. First vertical slice: stable cue outputs from the library

Idea: if BeatCue can create, validate, and write canonical cue data through a
library API before media analysis lands, the project will have stable output
contracts for every later detector.

This phase delivers a usable library surface for constructing an
`AnalysisResult` and writing BeatCue JSON plus WebVTT. It proves that the
domain model, schema, timestamps, and writer contracts are stable before the
package depends on heavy video libraries.

### 2.1. Implement the domain model and cue invariants

This step answers whether the core cue representation can carry all planned
outputs without adapter leakage. Its outcome informs the writer and application
services. See beatcue-technical-design.md §§4, 7, 8, and 17.

- [ ] 2.1.1. Implement immutable domain value objects for media, feature
  summaries, cues, objects, diagnostics, and provenance.
  - Requires steps 1.1-1.4.
  - See beatcue-technical-design.md §§4, 7, and 8.
  - Success: domain tests verify range, confidence, cue ID, and provenance
    invariants without importing adapter packages.
- [ ] 2.1.2. Implement cue fusion and stable ordering.
  - Requires 2.1.1.
  - Cover tolerance-based merging, same-kind overlap rules, annotation
    preservation, and feature merging.
  - See beatcue-technical-design.md §§7, 9, and 17.
  - Success: Hypothesis covers sorted, overlapping, and empty cue lists without
    producing unstable output order.

### 2.2. Deliver the BeatCue JSON and WebVTT writer loop

This step answers whether the canonical result can produce the two day-one
machine-readable formats. Its outcome informs CLI output and snapshot policy.
See beatcue-technical-design.md §13.

- [ ] 2.2.1. Implement BeatCue JSON serialization and validation.
  - Requires 2.1.1 and 1.1.1.
  - Include media metadata, cue arrays, diagnostics, configuration, and
    provenance.
  - See beatcue-technical-design.md §§13.1 and 17.
  - Success: syrupy snapshots lock the canonical fixture output and schema
    validation rejects non-finite values.
- [ ] 2.2.2. Implement WebVTT metadata cue writing.
  - Requires 2.2.1.
  - Use ASCII JSON payloads by default and millisecond timestamp rounding.
  - See beatcue-technical-design.md §§13.2 and 17.
  - Success: WebVTT snapshots preserve cue order, timestamps, cue IDs, and
    ASCII escaping.
- [ ] 2.2.3. Expose the library writer API.
  - Requires 2.2.1 and 2.2.2.
  - Provide a small public function that writes selected formats from an
    `AnalysisResult`.
  - See beatcue-technical-design.md §§2, 5, 8, and 13.
  - Success: a library caller can write JSON and WebVTT without importing
    Cyclopts, Rich, or filesystem-specific CLI code.

## 3. Second vertical slice: inspect and analyse media deterministically

Idea: if BeatCue can inspect a real video and emit deterministic cue sheets
from colour, motion, audio, and scene signals, the package will solve the core
timing problem before semantic models or async operations add complexity.

This phase introduces the media adapters and deterministic detectors. It
delivers a CLI path that can analyse real single-scene or single-shot files
with no VLM dependency. This deterministic-only product is the v1 boundary and
is useful on its own before semantic or object enrichment lands.

### 3.1. Probe media and extract aligned inputs

This step answers whether BeatCue can establish a trustworthy timeline from
real media. Its outcome informs every detector that relies on timestamps. See
beatcue-technical-design.md §§9, 10, 16, and 18.

- [ ] 3.1.1. Implement the Cuprum-backed `ffprobe` media probe adapter.
  - Requires 1.4.3 and 2.1.1.
  - Parse JSON output into domain media metadata and structured diagnostics.
  - See beatcue-technical-design.md §§8, 9, 16, and 18.
  - Success: CmdMox tests cover success, missing binary, malformed JSON, and
    unsupported media without parsing stderr as data.
- [ ] 3.1.2. Implement frame sampling with source timestamps.
  - Requires 3.1.1.
  - Preserve sample timestamps and report partial-read failures explicitly.
  - See beatcue-technical-design.md §§8-10 and 18.
  - Success: generated media fixtures produce monotonic timestamps tied to the
    probed duration.
- [ ] 3.1.3. Implement `ffmpeg` audio extraction and librosa feature loading.
  - Requires 3.1.1 and 1.4.3.
  - Return RMS, onset strength, tempo, beat times, or a no-audio diagnostic.
  - See beatcue-technical-design.md §§9, 10, 16, and 18.
  - Success: no-audio inputs keep visual analysis available and redistribute
    audio weights as specified.

### 3.2. Detect deterministic timing cues

This step answers whether colour, motion, audio, and scene signals can produce
useful cue sheets without semantic models. Its outcome informs semantic
keyframe selection. See beatcue-technical-design.md §§9-11.

- [ ] 3.2.1. Implement colourgram extraction and visual event candidates.
  - Requires 3.1.2.
  - Compute colour histograms, luminance, saturation, contrast, edge density,
    and adjacent-frame deltas.
  - See beatcue-technical-design.md §§9 and 10.
  - Success: fixtures with hard cuts, fades, and flashes produce explainable
    feature summaries.
- [ ] 3.2.2. Implement dense motion extraction and camera-motion summaries.
  - Requires 3.1.2.
  - Compute optical-flow magnitude, p90 magnitude, global flow, and
    camera-motion estimates.
  - See beatcue-technical-design.md §§9-11.
  - Success: static, pan, and high-motion fixtures produce distinguishable
    motion features.
- [ ] 3.2.3. Implement scene and beat candidate detection.
  - Requires 3.1.3 and 3.2.1.
  - Integrate PySceneDetect for scene candidates and librosa beat/onset
    features for audio cues.
  - See beatcue-technical-design.md §§9 and 10.
  - Success: deterministic fixtures emit cut and beat cues with provenance.
- [ ] 3.2.4. Implement action intensity, ease, and action-arc classification.
  - Requires 3.2.1, 3.2.2, and 3.2.3.
  - Fit ease curves, classify rising and falling action, and emit action peaks.
  - See beatcue-technical-design.md §§10, 11, and 17.
  - Success: property tests cover slope thresholds, minimum durations, and
    confidence bounds over generated intensity curves.

### 3.3. Deliver the deterministic `analyse` CLI loop

This step answers whether a user or agent can run BeatCue end to end on a local
file and receive bounded, parseable output. Its outcome informs later
agent-native operations. See beatcue-technical-design.md §§13-18.

- [ ] 3.3.1. Implement `beatcue inspect VIDEO`.
  - Requires 3.1.1.
  - Emit human output through Rich and machine output through `--json`.
  - See beatcue-technical-design.md §§13.4, 14, 16, and 18.
  - Success: diagnostics go to standard error and JSON data goes to standard
    output.
- [ ] 3.3.2. Implement `beatcue analyse VIDEO` for deterministic outputs.
  - Requires 2.2.3 and 3.2.4.
  - Support `--out`, `--json-out`, `--sample-fps`, `--include-series`, and
    `--force`.
  - See beatcue-technical-design.md §§9, 13, 14, and 18.
  - Success: a real sample video produces WebVTT and BeatCue JSON without VLM
    dependencies.
- [ ] 3.3.3. Add an end-to-end deterministic fixture suite.
  - Requires 3.3.2.
  - Cover no-audio, hard-cut, fade, beat, motion-ramp, partial-failure, and
    existing-output cases.
  - See beatcue-technical-design.md §§17 and 18.
  - Success: the suite proves the CLI, library, writers, and deterministic
    adapters agree on cue IDs and diagnostics.

## 4. Third vertical slice: agent-native configuration and operations

Idea: if BeatCue can be driven repeatedly by agents with inspectable command
shape, persistent profiles, recoverable jobs, and bounded outputs, the CLI will
be dependable automation infrastructure rather than a human-only wrapper.

This phase completes the CLI behaviours that make BeatCue usable from scripts,
agents, and continuous integration. It builds on the deterministic analysis
loop instead of introducing new detection algorithms.

### 4.1. Implement typed configuration and profiles

This step answers whether users can carry analysis preferences across
invocations without losing deterministic precedence. Its outcome informs async
jobs and `agent-context`. See beatcue-technical-design.md §§14 and 15.

- [ ] 4.1.1. Implement Cyclopts configuration binding for root and command
  options.
  - Requires 3.3.2.
  - Merge explicit flags, environment variables, profiles, config files, and
    defaults in the documented order.
  - See beatcue-technical-design.md §§14 and 15.
  - Success: Hypothesis covers precedence combinations without ambiguous wins.
- [ ] 4.1.2. Implement profile storage and `profile` subcommands.
  - Requires 4.1.1.
  - Add `profile list`, `profile show`, `profile save`, and `profile delete`.
  - See beatcue-technical-design.md §§8, 14, and 15.
  - Success: profile commands support `--json`, reject invalid values with
    enumerated choices, and never store secrets.

### 4.2. Make the CLI self-describing and recovery-friendly

This step answers whether an agent can discover BeatCue's command surface and
recover from interrupted work without scraping help text. Its outcome informs
combinatorial CLI validation. See beatcue-technical-design.md §§14, 15, and 18.

- [ ] 4.2.1. Implement `agent-context`.
  - Requires 4.1.2.
  - Include schema version, commands, flags, enum values, output formats,
    profiles, delivery schemes, and exit codes.
  - See beatcue-technical-design.md §14.
  - Success: syrupy snapshots lock the public `agent-context` shape.
- [ ] 4.2.2. Implement the JSON Lines job ledger and `jobs` subcommands.
  - Requires 4.1.1.
  - Add `jobs list`, `jobs get`, and `jobs prune` with bounded output.
  - See beatcue-technical-design.md §§8, 14, 15, and 18.
  - Success: interrupted `--wait` runs leave recoverable job state.
- [ ] 4.2.3. Implement `--wait` for long-running analysis.
  - Requires 4.2.2 and 3.3.2.
  - Record submission, progress, completion, and failure states in the ledger.
  - See beatcue-technical-design.md §§14, 15, and 18.
  - Success: retrying after interruption reports the existing job rather than
    starting an indistinguishable duplicate.

### 4.3. Cover the CLI combination surface

This step answers whether the agent-native behaviours remain consistent across
flags, profiles, output modes, and delivery targets. Its outcome informs v1
release readiness. See beatcue-technical-design.md §§14-18.

- [ ] 4.3.1. Implement delivery and feedback commands.
  - Requires 4.2.1.
  - Add `--deliver=stdout`, `--deliver=file:<path>`, feedback recording, and
    structured refusal for unsupported schemes.
  - See beatcue-technical-design.md §§14, 15, 18, and 19.
  - Success: file delivery writes atomically and unsupported schemes enumerate
    the accepted set.
- [ ] 4.3.2. Add the CLI combinatorial behaviour suite.
  - Requires 4.1.2, 4.2.3, and 4.3.1.
  - Cover `--json`, `--plain`, `--no-input`, `--force`, `--wait`,
    `--profile`, config files, delivery schemes, and output collisions.
  - See beatcue-technical-design.md §§14-18.
  - Success: pytest-bdd scenarios prove stdout/stderr separation, bounded list
    output, valid enum errors, and deterministic precedence across high-risk
    combinations.

## 5. Fourth vertical slice: semantic and editorial enrichment

Idea: if BeatCue can add captions, object cues, and OTIO markers without
allowing model output to create unsupported timing events, the package can
serve richer editorial workflows while preserving deterministic trust.

This phase adds optional model-backed enrichment and editorial interchange. It
must keep semantic output subordinate to deterministic cue candidates.

### 5.1. Add semantic annotation behind ports

This step answers whether model-backed annotations can enrich cues without
leaking model packages into the domain. Its outcome informs object cues and
OTIO metadata. See beatcue-technical-design.md §§8, 9, 12, 17, and 19.

- [ ] 5.1.1. Implement semantic keyframe selection.
  - Requires 3.2.4.
  - Select keyframes at scene starts, cuts, action peaks, object entries/exits,
    and high colour-delta points.
  - See beatcue-technical-design.md §§9 and 12.
  - Success: keyframe selection is deterministic for a fixed cue list and
    configuration.
- [ ] 5.1.2. Implement the local caption adapter contract.
  - Requires 5.1.1 and 1.1.3.
  - Validate structured model responses, provenance, enum values, ASCII output
    policy, local model availability, and no implicit remote downloads.
  - See beatcue-technical-design.md §§8, 12, 17, and 19.
  - Success: invalid model output records diagnostics and cannot create timing
    cues; missing local model weights fail before inference with an actionable
    diagnostic.

### 5.2. Add object entry and exit cues

This step answers whether object observations can generate entry and exit cues
with enough persistence to avoid one-frame false positives. Its outcome informs
editorial markers and future tracking extensions. See
beatcue-technical-design.md §§8, 11, 12, 17, and 21.

- [ ] 5.2.1. Implement the v1 object tracker adapter selected by ADR.
  - Requires 1.1.2 and 3.1.2.
  - Return track IDs, labels, boxes, centroids, velocities, and confidence.
  - See beatcue-technical-design.md §§8, 11, 12, and 21.
  - Success: object observations remain domain-owned and do not expose adapter
    library types.
- [ ] 5.2.2. Implement entry and exit cue classification.
  - Requires 5.2.1.
  - Enforce frame-edge margins, minimum persistence, and camera-compensated
    speed where available.
  - See beatcue-technical-design.md §§10, 11, and 17.
  - Success: fixtures distinguish true entries/exits from transient detections
    and camera pans.

### 5.3. Deliver editorial interchange through OTIO

This step answers whether BeatCue cues can travel into editorial tooling with
the same IDs, confidence, annotations, and provenance as JSON and WebVTT. See
beatcue-technical-design.md §§13 and 17.

- [ ] 5.3.1. Implement OTIO marker writing.
  - Requires 2.2.3 and 5.1.2.
  - Store cue metadata under a BeatCue namespace on timeline or clip markers.
  - See beatcue-technical-design.md §13.3.
  - Success: OTIO snapshots or summaries preserve cue IDs, timing, kind,
    confidence, annotation, features, and provenance.
- [ ] 5.3.2. Add an enrichment end-to-end suite.
  - Requires 5.2.2 and 5.3.1.
  - Cover deterministic cues with captions, invalid captions, object entries,
    object exits, WebVTT, BeatCue JSON, and OTIO output in one workflow.
  - See beatcue-technical-design.md §§12, 13, 17, and 18.
  - Success: semantic annotation enriches existing cues and never creates a
    cue without deterministic timing evidence.

## 6. Deferred extensions after the core v1 promise

Idea: if the core v1 promise is already trustworthy and boring to operate,
BeatCue can evaluate broader model, hardware, and tracking extensions on their
product value instead of letting them destabilize the main release.

This phase collects work the design explicitly defers. Items here should not
move earlier without an ADR updating the v1 boundary.

### 6.1. Evaluate remote and accelerated model execution

This step answers whether remote or GPU-backed model execution belongs in a
post-v1 BeatCue without weakening privacy and reproducibility guarantees. See
beatcue-technical-design.md §§19 and 21.

- [ ] 6.1.1. Design the remote model credentials and privacy boundary.
  - Requires phase 5.
  - See beatcue-technical-design.md §§19 and 21.
  - Success: one design or ADR defines secret storage, prompt retention,
    payload logging, and opt-in behaviour before remote execution is allowed.
- [ ] 6.1.2. Evaluate GPU scheduling and model capability discovery.
  - Requires phase 5.
  - See beatcue-technical-design.md §21.
  - Success: BeatCue can report unavailable hardware as a capability mismatch
    rather than an opaque model failure.

### 6.2. Evaluate advanced tracking and genre profiles

This step answers whether heavier video tracking and trainable profiles earn
their complexity after deterministic v1 cues exist. See
beatcue-technical-design.md §§10, 11, and 21.

- [ ] 6.2.1. Evaluate SAM 2 or equivalent video segmentation for persistent
  object tracking.
  - Requires 5.2.2.
  - See beatcue-technical-design.md §§11 and 21.
  - Success: a comparison report shows whether advanced tracking improves
    entry/exit precision enough to justify the dependency.
- [ ] 6.2.2. Design trainable genre profiles for action-intensity weights.
  - Requires phase 5.
  - See beatcue-technical-design.md §§10, 15, and 21.
  - Success: one design defines training data, evaluation metrics, profile
    migration, and fallback behaviour for deterministic defaults.
