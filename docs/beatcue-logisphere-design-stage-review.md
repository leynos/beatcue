# BeatCue Logisphere design-stage review

- Status: Complete
- Date: 2026-05-09
- Documents reviewed:
  - `docs/beatcue-technical-design.md` (draft, 2026-05-09)
  - `docs/roadmap.md`
- Panel: Full (Pandalump, Wafflecat, Buzzy Bee, Telefono, Doggylump, Dinolump)

## 1. Proposal summary

BeatCue is a Python package and CLI for extracting editorial timing cues from
video files. It produces WebVTT metadata cues, OpenTimelineIO markers, and a
lossless BeatCue JSON format from a single canonical analysis result. The
design uses hexagonal architecture with twelve driven ports, a two-pass
action-intensity pipeline (deterministic first, then semantic enrichment), and
an agent-native CLI built on Cyclopts with non-interactive defaults.

The repository currently contains a package skeleton with a smoke-check
function, comprehensive design documentation, and a phased roadmap. No
production code exists yet.

## 2. Core bets

The design makes these bets explicitly or implicitly:

1. **Hexagonal purity is worth the cost.** Twelve domain-owned port protocols
   and strict import boundaries will survive contact with the messy reality of
   NumPy arrays, OpenCV frames, and Transformers model outputs without becoming
   an adapter translation tax.
2. **Deterministic signals first.** The two-pass pipeline — deterministic cues
   before semantic annotation — will produce useful output without any VLM, and
   semantic signals can be meaningfully subordinated to timing evidence.
3. **Local-only execution is sufficient for v1.** Users will accept running
   7B-parameter VLMs and Florence-2 on local hardware. GPU scheduling and
   remote inference are deferred.
4. **A single developer (or very small team) can deliver this.** The roadmap
   has six phases, roughly fifty tasks, twelve adapters, three output formats,
   six CLI command groups, and integrations with FFmpeg, OpenCV, librosa,
   PySceneDetect, Florence-2, Qwen2.5-VL, OpenTimelineIO, Cyclopts, Rich,
   Cuprum, and CmdMox.
5. **Canonical in-memory result as single source of truth.** All three output
   formats derive from one `AnalysisResult` object, and that object can carry
   everything from raw feature series to semantic annotations.
6. **Cuprum and CmdMox are production-ready for this use case.** The design
   delegates all subprocess execution to these libraries, which appear to be
   maintained by the same developer.

## 3. Panel findings

### 3.1. Pandalump 🐼 — Structural integrity

**Dependency direction is clear and enforceable.** The hexagonal boundary is
well-drawn. The design names a CI fitness function for import checking, and the
roadmap schedules it early (task 1.2.2). The dependency rule — domain imports
only stdlib and other domain modules — is stated plainly and can be checked
statically.

**The domain model is coherent.** `TimeRange`, `Cue`, `CueKind`,
`ObjectObservation`, and `AnalysisResult` form a consistent vocabulary. Names
describe intent rather than implementation. The frozen dataclass approach keeps
domain objects immutable.

- 🟡 **Twelve ports is a lot for a v1.** The port surface
  (`MediaProbe`, `FrameSampler`, `AudioExtractor`, `AudioFeatureExtractor`,
  `SceneDetector`, `MotionExtractor`, `ObjectTracker`, `SemanticAnnotator`,
  `CueWriter`, `JobLedger`, `ProfileStore`, `CommandRunner`) is comprehensive,
  but some ports may be premature. `AudioExtractor` and `AudioFeatureExtractor`
  could be one port until a second audio backend exists. `JobLedger` and
  `ProfileStore` are persistence ports that will each have exactly one
  implementation for the foreseeable future. The design should acknowledge
  which ports exist because they have real substitutability requirements, and
  which exist for testing convenience alone.

- 🟢 **The `AnalyseVideo` service dataclass is load-bearing.** Its constructor
  takes nine injected dependencies. This is honest about the pipeline's
  complexity, but it makes composition root wiring verbose. Consider whether a
  pipeline-builder or a smaller struct-of-structs grouping (e.g. a
  `MediaInputs` bundle for probe + sampler + audio) would reduce the
  composition surface without hiding dependencies.

- 🟢 **`beatcue.config` as composition root is well-placed.** Keeping it
  separate from CLI and application layers is correct. The design should state
  explicitly that `config` may import adapters (it is the only package that
  should).

- 💡 **The colourgram is domain or adapter?** The design describes the
  colourgram vector contents (§10) but does not say whether `Colourgram` is a
  domain value object or an adapter-internal structure. If domain services
  operate on colourgram data for action-intensity computation, it needs a
  domain representation. If it is only an intermediate adapter artefact, it
  should not appear in the domain terminology table.

### 3.2. Wafflecat 🐈🧇 — Alternative futures

- 🟡 **No alternatives section in the design.** The document does not record
  which architectural alternatives were considered and rejected. Hexagonal
  architecture is presented as a given, not a decision. A short ADR or
  "Alternatives considered" section would strengthen reviewer confidence that
  simpler options (a flat pipeline module, a plugin-based architecture, or a
  dataflow-graph approach) were evaluated.

- 🟡 **The 80/20 version is buried.** A simpler BeatCue that runs
  `ffprobe` + PySceneDetect + librosa beat detection and writes WebVTT would
  deliver substantial value with three adapters instead of twelve. The design
  describes this path implicitly (phase 3 of the roadmap) but does not frame it
  as a viable standalone product. If the project stalls after phase 3, is that
  a useful tool or an incomplete skeleton? The roadmap's phase 2 idea statement
  comes closest to acknowledging this, but the design itself does not.

- 🟢 **Dataflow-graph alternative.** BeatCue's pipeline is a directed acyclic
  graph: probe → sample → (colour, motion, audio, scene) → intensity →
  keyframes → annotation → final intensity → fusion → write. An explicit DAG
  scheduler (even a simple topological-sort executor) would make dependencies
  between steps data-driven rather than procedural, and would make partial
  re-runs (e.g. re-annotate without re-extracting features) straightforward.
  This is not necessarily better for v1, but it is a genuine alternative that
  trades implementation simplicity for extensibility.

- 💡 **Prior art.** The design does not reference existing video-analysis
  pipelines that solve structurally similar problems (e.g. MoviePy for
  composition, Whisper for audio transcription pipelines, or academic beat
  detection tools). Acknowledging prior art would help reviewers understand
  where BeatCue's approach diverges intentionally.

### 3.3. Buzzy Bee 🐝 — Scaling and cost

- 🟡 **No load profile or resource estimates.** The design does not state
  expected input sizes (video duration, resolution, frame rate) or processing
  costs. A 30-second trailer and a 2-hour film have vastly different memory and
  compute profiles. Frame sampling at 4 fps on a 2-hour file produces 28,800
  frames; dense optical flow on those frames may exhaust memory on a typical
  workstation. The design should state target input bounds or describe how the
  pipeline degrades for large inputs.

- 🟡 **Feature-series storage is unbounded by default.** The `--include-series`
  flag gates large arrays, but the default `AnalysisResult` still carries
  colourgram summaries, motion summaries, and audio features for every sampled
  frame. The design should clarify whether the in-memory result is bounded or
  whether it accumulates proportionally to video length.

- 🟢 **VLM inference is the obvious bottleneck.** Running Qwen2.5-VL-7B
  locally is slow even with GPU acceleration. The design correctly makes
  semantic annotation optional, but the keyframe selection strategy (§9, step
  9) could produce dozens of keyframes on a long video, each requiring a
  model forward pass. A configurable cap on keyframe count would prevent
  runaway inference time.

- 🟢 **Optical flow is memory-intensive.** Farneback dense optical flow
  allocates a float32 flow field the size of each frame pair. For 1080p input,
  that is roughly 16 MB per frame pair. The design should note whether flow is
  computed incrementally (frame-by-frame, discarding previous results) or
  accumulated.

### 3.4. Telefono ☎️ — Contracts and interfaces

**The output contracts are well-defined.** WebVTT uses ASCII JSON payloads by
default. BeatCue JSON is the lossless interchange format. OTIO writes through
the library rather than hand-crafting JSON. The design commits to syrupy
snapshots for all three, which is the right level of contract enforcement for a
pre-1.0 project.

- 🔴 **`AnalysisResult` schema is unspecified.** The design describes `Cue`,
  `TimeRange`, `ObjectObservation`, and `CueKind` as domain value objects, but
  `AnalysisResult` — the canonical object from which all outputs derive — is
  never defined. Its fields, invariants, and serialization contract are absent.
  This is the single most important data structure in the system. It should
  appear in §7 alongside `Cue`.

- 🟡 **Schema technology is deferred too long.** The design lists the BeatCue
  JSON schema mechanism as a deferred decision (§21), but the roadmap requires
  it for task 1.1.1 and every writer task depends on it. This is not truly
  deferred — it is blocking. The distinction between "deferred for v1" and
  "must decide before implementation starts" should be explicit.

- 🟡 **`agent-context` contract is described but not specified.** The design
  says `agent-context` includes schema version, commands, flags, enum values,
  profiles, delivery schemes, and exit codes (§14). But the document does not
  define the JSON shape, versioning strategy, or compatibility promise. Since
  `agent-context` exists specifically for machine consumers, its contract needs
  more rigour than a bullet list.

- 🟢 **WebVTT timestamp precision is correct.** Rounding to milliseconds and
  preventing start-after-end is the right invariant. The design should confirm
  whether timestamps are truncated or rounded (they are different operations
  for values like 3.2395 seconds).

- 🟢 **Cue ID stability is a strong contract.** The promise that cue IDs are
  deterministic for a given input, configuration, and cue ordering enables
  snapshot testing and diff-based workflows. The design should describe the ID
  generation algorithm (hash-based, sequence-based, or composite) so
  implementers do not make incompatible choices.

- 💡 **Port protocol definitions are absent.** The design lists twelve ports
  by name and responsibility (Table 2) but does not show their method
  signatures. `MediaProbe` presumably returns domain media metadata, but the
  input and output types are not specified. Port protocols should be defined at
  least as precisely as `Cue` is.

### 3.5. Doggylump 🐶 — Failure modes and operations

**The failure mode table (§18) is strong.** Seven explicit failure scenarios
with defined behaviour is better than most designs at this stage. The design
correctly requires failing before side effects for dependency errors.

- 🟡 **`--partial` mode is under-specified.** The design says partial mode
  "writes diagnostics and marks outputs incomplete" but does not say how
  outputs are marked. Is the BeatCue JSON schema extended with a completion
  flag? Does WebVTT include a note? Can downstream consumers distinguish
  partial from complete output without out-of-band knowledge?

- 🟡 **Job ledger corruption.** The design uses JSON Lines for the job ledger
  to avoid corruption from interrupted writes. This is a reasonable choice, but
  it does not address concurrent writes from multiple BeatCue processes
  targeting the same ledger file. File locking or per-process ledger files
  would prevent interleaving.

- 🟢 **Model download failures are not addressed.**

  If a caption model such as `Qwen/Qwen2.5-VL-7B-Instruct` is specified and is
  not cached locally, Transformers will attempt to download it. The design
  should state whether BeatCue catches download failures, whether it requires
  pre-downloaded models, or whether it delegates entirely to Transformers'
  error handling.

- 🟢 **Disk space exhaustion during writing.** The design requires atomic
  writes for delivery adapters but does not address partial writes when disk
  space runs out mid-file. Atomic writes via temp-file-then-rename handle this
  correctly if implemented, but the design should state the mechanism.

- 💡 **No graceful degradation for missing optional adapters.** The design says
  "BeatCue fails only if the user explicitly requested that model" (§18), but
  it does not say what happens when PySceneDetect or OpenCV is not installed.
  Are these required dependencies or optional? The `pyproject.toml` currently
  lists no runtime dependencies at all.

### 3.6. Dinolump 🦕 — Long-term viability and team impact

- 🔴 **Scope-to-team mismatch.** The design specifies twelve adapter
  integrations across five infrastructure domains (media processing, computer
  vision, audio analysis, ML inference, file I/O), a six-command CLI with
  profile management and job recovery, three output formats, and a two-pass
  analysis pipeline. The `pyproject.toml` shows no runtime dependencies yet.
  The gap between design ambition and current implementation is large. Without
  an explicit statement of team size and capacity, the roadmap risks being an
  aspirational document rather than a delivery plan. The design should scope a
  credible v1 boundary — possibly just phases 1–3 of the roadmap — and call
  everything else post-v1.

- 🟡 **Dependency breadth is high.** The runtime dependency set includes
  Cyclopts, Rich, Cuprum, OpenTimelineIO, OpenCV, librosa, PySceneDetect,
  Transformers, Florence-2, and Qwen2.5-VL. Several of these (Transformers,
  Florence-2, Qwen2.5-VL) pull in PyTorch and hundreds of transitive
  dependencies. The design should distinguish required from optional
  dependencies and specify dependency groups so a minimal installation (no VLM,
  no object tracking) remains lightweight.

- 🟡 **Cuprum and CmdMox are single-maintainer dependencies.** The design
  delegates all subprocess execution to Cuprum and all subprocess testing to
  CmdMox. Both appear to be maintained by the same developer who is building
  BeatCue. This is fine for internal tooling but creates a bus-factor risk for
  external contributors. The design should acknowledge this and note whether
  the port abstraction allows swapping Cuprum for direct subprocess calls if
  needed.

- 🟢 **The testing strategy is well-matched to the architecture.** Using
  Hypothesis for domain invariants, CmdMox for subprocess contracts, syrupy for
  output stability, and pytest-bdd for CLI workflows is a coherent verification
  stack. The concern is whether the team has bandwidth to write all these test
  types for all twelve adapters.

- 🟢 **The hexagonal boundary reduces cognitive load per layer.** A developer
  working on the librosa adapter does not need to understand the Cyclopts CLI
  or the OTIO writer. This is a genuine benefit of the architecture — provided
  the port protocols are well-documented enough that adapter authors can work
  from contracts rather than reading application code.

## 4. Pre-mortem (Doggylump leads)

> It is six months from now. BeatCue has caused a significant problem. Working
> backwards:

### Scenario A: The incomplete product

**What happened:** After six months, phases 1 and 2 are complete. The domain
model is solid, writers work, and snapshot tests pass. But no real video has
been analysed because phase 3 adapter work (OpenCV, librosa, PySceneDetect
integration) proved harder than expected — frame timestamp alignment issues,
librosa version incompatibilities, and PySceneDetect API changes consumed the
available effort. The project has a well-architected skeleton that cannot
process a video file.

**Root cause:** The design bet that twelve ports and three output formats were
all v1 requirements. The roadmap's phase ordering (contracts first, then
writers, then media) was architecturally logical but delayed the riskiest
integration work.

**Signal missed:** No spike or prototype validated that the adapter
integrations work before the full architecture was built.

**Mitigation:** Add a "walking skeleton" task to phase 1 that runs `ffprobe` →
sample one frame → write a single-cue WebVTT file through the full pipeline.
This proves the hexagonal plumbing works with real I/O before investing in
domain model polish.

### Scenario B: Memory exhaustion on real media

**What happened:** A user ran `beatcue analyse` on a 90-minute documentary. The
pipeline sampled 21,600 frames at 4 fps, computed dense optical flow for each
pair, and accumulated all feature arrays in the `AnalysisResult`. The process
consumed 32 GB of memory and was killed by the OS.

**Root cause:** The design does not specify memory management for the feature
pipeline. The `AnalysisResult` carries all features in memory until writers
flush.

**Signal missed:** No input-size bounds or memory-budget analysis in the design.

**Mitigation:** Define maximum input duration or resolution tiers in the
default profile. Process features in sliding windows rather than accumulating
full arrays. Gate large feature retention behind `--include-series` at the
in-memory level, not just at serialization time.

### Scenario C: Semantic cues override deterministic evidence

**What happened:** A VLM returned `action_intensity: 0.95` for a static
establishing shot. Because the semantic weight (`w_semantic = 0.05`) was low,
this should not have created a cue — but a bug in weight redistribution when
object tracking was disabled inflated the effective semantic weight. The
resulting cue sheet contained false action peaks that misled a downstream
editing agent.

**Root cause:** The weight redistribution logic (§10) is described in prose but
not formally specified. The invariant "semantic annotations cannot create
timing cues without deterministic evidence" is stated, but the enforcement
mechanism is not defined.

**Signal missed:** No property test covering weight redistribution under all
combinations of disabled signals.

**Mitigation:** Express the redistribution rule as a testable function with
Hypothesis coverage over all signal-availability combinations. Add an explicit
assertion that the effective semantic contribution alone cannot exceed the
action-peak threshold.

## 5. Alternatives checkpoint (Wafflecat leads)

### Strongest alternative: pipeline-as-DAG with lazy evaluation

Instead of a procedural two-pass pipeline orchestrated by `AnalyseVideo.run()`,
define the analysis as a directed acyclic graph of typed stages. Each stage
declares its inputs (other stages or source media) and its output type.
Execution proceeds by topological sort, with optional caching of intermediate
results.

**What it gains:**

- Partial re-runs: re-annotate without re-extracting features.
- Explicit parallelism: independent stages (colour and audio) can run
  concurrently without manual orchestration.
- Memory control: completed stages can be evicted once all dependents have
  consumed their output.
- Extensibility: adding a new detector is adding a node, not editing a method.

**What it trades away:**

- Simplicity: a DAG executor is more complex than a linear method.
- Debuggability: stage-by-stage execution is harder to step through.
- Design consistency: the hexagonal ports-and-adapters model does not naturally
  compose with a dataflow graph; the two paradigms would need reconciliation.

**Assessment:** The current procedural pipeline is the right choice for v1. The
DAG alternative becomes compelling if BeatCue needs pluggable detector chains
or incremental re-analysis post-v1. The current port design does not preclude
migrating to a DAG executor later, since ports already abstract the individual
stages.

## 6. Verdict

⚠️ **Proceed with conditions.**

The design is thorough, well-structured, and makes good architectural
decisions. The hexagonal boundary is clearly drawn. The domain model is
coherent. The output contracts are well-specified. The failure mode analysis is
better than average. The roadmap is realistic in its sequencing, though
ambitious in its total scope.

The conditions below must be addressed before or during early implementation.

## 7. Findings summary

### Design flaws (🔴)

| #   | Finding                                                                                                                                                            | Expert      | Section   |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------- | --------- |
| 1   | `AnalysisResult` — the single most important data structure — is never defined. Its fields, invariants, and serialization contract are absent from §7.             | Telefono ☎️ | §7        |
| 2   | Scope-to-team mismatch: twelve adapters, six command groups, three output formats, and two ML model integrations with no stated team size or explicit v1 boundary. | Dinolump 🦕 | §§5–6, 20 |

_Table 1: Design flaws._

### Unresolved risks (🟡)

| #   | Finding                                                                                                                              | Expert         | Section    |
| --- | ------------------------------------------------------------------------------------------------------------------------------------ | -------------- | ---------- |
| 3   | Twelve ports may be premature; some (e.g. `AudioExtractor` / `AudioFeatureExtractor`) have no real substitutability requirement yet. | Pandalump 🐼   | §8         |
| 4   | No alternatives section in the design; hexagonal architecture is presented as given, not as a decision.                              | Wafflecat 🐈🧇 | §5         |
| 5   | No load profile or resource estimates; unbounded input sizes can exhaust memory.                                                     | Buzzy Bee 🐝   | §§9–10     |
| 6   | In-memory feature-series storage is unbounded and grows proportionally to video length.                                              | Buzzy Bee 🐝   | §10        |
| 7   | Schema technology for BeatCue JSON is listed as deferred (§21) but is actually blocking (roadmap 1.1.1).                             | Telefono ☎️    | §§13.1, 21 |
| 8   | `agent-context` contract is described but its JSON shape, versioning, and compatibility promise are not specified.                   | Telefono ☎️    | §14        |
| 9   | `--partial` mode does not say how outputs are marked incomplete for downstream consumers.                                            | Doggylump 🐶   | §18        |
| 10  | Job ledger does not address concurrent writes from multiple BeatCue processes.                                                       | Doggylump 🐶   | §15        |
| 11  | Dependency breadth is high; no distinction between required and optional runtime dependencies.                                       | Dinolump 🦕    | §§5, 20    |
| 12  | Cuprum and CmdMox are single-maintainer dependencies with bus-factor risk.                                                           | Dinolump 🦕    | §16        |
| 13  | The 80/20 product (probe + scene detect + beat detect → WebVTT) is not framed as a viable standalone deliverable.                    | Wafflecat 🐈🧇 | §§9, 20    |

_Table 2: Unresolved risks._

### Improvements (🟢)

| #   | Finding                                                                                                             | Expert       | Section |
| --- | ------------------------------------------------------------------------------------------------------------------- | ------------ | ------- |
| 14  | Consider grouping related port dependencies (e.g. `MediaInputs` bundle) to reduce `AnalyseVideo` constructor arity. | Pandalump 🐼 | §8      |
| 15  | State explicitly that `beatcue.config` is the only package permitted to import adapters.                            | Pandalump 🐼 | §5      |
| 16  | Cap the number of semantic keyframes to prevent runaway VLM inference on long videos.                               | Buzzy Bee 🐝 | §9      |
| 17  | Clarify whether optical flow is computed incrementally or accumulated.                                              | Buzzy Bee 🐝 | §10     |
| 18  | Confirm whether WebVTT timestamps are truncated or rounded.                                                         | Telefono ☎️  | §13.2   |
| 19  | Describe the cue ID generation algorithm.                                                                           | Telefono ☎️  | §7      |
| 20  | Address model download failures when `--caption-model` specifies a model not cached locally.                        | Doggylump 🐶 | §18     |
| 21  | State the atomic-write mechanism for delivery adapters.                                                             | Doggylump 🐶 | §19     |
| 22  | The testing strategy is well-matched to the architecture; concern is bandwidth to write all test types.             | Dinolump 🦕  | §17     |
| 23  | The hexagonal boundary reduces cognitive load per layer, provided port protocols are well-documented.               | Dinolump 🦕  | §5      |

_Table 3: Improvements._

### Open questions (💡)

| #   | Finding                                                                                     | Expert         | Section |
| --- | ------------------------------------------------------------------------------------------- | -------------- | ------- |
| 24  | Is the colourgram a domain value object or an adapter-internal structure?                   | Pandalump 🐼   | §§4, 10 |
| 25  | What prior art was evaluated?                                                               | Wafflecat 🐈🧇 | —       |
| 26  | Port protocol method signatures are absent; implementers lack input/output type contracts.  | Telefono ☎️    | §8      |
| 27  | What happens when PySceneDetect or OpenCV is not installed? Are these required or optional? | Doggylump 🐶   | §18     |

_Table 4: Open questions._

## 8. Recommended next steps

1. **Define `AnalysisResult` in §7.** This is the canonical object; all
   writers, all tests, and all application services depend on it. Define its
   fields and invariants before implementation starts. (Addresses finding 1.)

2. **Draw the v1 boundary explicitly.** State that phases 1–3 (plus phase 4
   for CLI polish) constitute the v1 release. Frame phases 5–6 as post-v1
   enrichment. Acknowledge that the deterministic-only product (no VLM, no
   object tracking) is a useful standalone deliverable. (Addresses findings 2,
   11, and 13.)

3. **Decide the schema technology now, not later.** The roadmap already
   requires this at task 1.1.1. Remove it from §21 (deferred decisions) and
   make it an early ADR. (Addresses finding 7.)

4. **Add input-size bounds or memory-budget guidance.** State the target input
   range (e.g. videos up to 30 minutes at 1080p for default settings) and
   describe how the pipeline handles longer inputs (lower sample rate, windowed
   processing, or explicit rejection). (Addresses findings 5 and 6.)

5. **Add a walking-skeleton task to phase 1.** Run `ffprobe` → sample one
   frame → emit a single-cue WebVTT through the full hexagonal pipeline. This
   validates the architecture with real I/O before investing in domain polish.
   (Addresses pre-mortem scenario A.)

6. **Specify port protocol signatures.** Define input and output types for at
   least the four riskiest ports (`MediaProbe`, `FrameSampler`,
   `AudioFeatureExtractor`, `CueWriter`) so adapter implementers can work from
   contracts. (Addresses findings 3 and 26.)

7. **Distinguish required from optional dependencies.** Define dependency
   groups in `pyproject.toml` so a minimal installation works without PyTorch,
   Transformers, or OpenCV. (Addresses findings 11 and 27.)

8. **Add weight-redistribution property tests early.** The invariant
   "semantic annotations cannot create timing cues without deterministic
   evidence" is critical. Specify the redistribution function formally and
   cover it with Hypothesis before building the intensity pipeline. (Addresses
   pre-mortem scenario C.)
