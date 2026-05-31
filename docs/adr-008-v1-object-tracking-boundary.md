# Architectural decision record (ADR) 008: v1 object-tracking boundary

## Status

Accepted. BeatCue records a domain-owned `ObjectTracker` port as the selected
object-tracking boundary for post-v1 implementation work. The first tracker
implementation should be a simple centroid-association default fed by detector
observations, while Florence-2 remains a detection and labelling adapter rather
than the tracking persistence boundary.

## Date

2026-05-17.

## Context and problem statement

BeatCue v1 is scoped to deterministic cue extraction for single-scene or
single-shot videos. Object tracking, object-entry cues, and object-exit cues
remain post-v1 implementation work, but later roadmap tasks need one selected
boundary before they can build tracking behaviour without reopening the model
adapter decision.

The unresolved choice is whether object tracking should mean image-level
Florence-2 detections, a concrete centroid tracker, or a pluggable tracker port
owned by the domain. The decision has to preserve BeatCue's hexagonal
architecture: the domain can own plain tracking concepts and protocols, but it
must not depend on OpenCV, Transformers, Torch, Pillow, or other adapter
objects.

## Decision drivers

- Object-entry and object-exit cues require persistence across frames; a single
  detection near a frame boundary is not enough evidence.
- The first implementation must be small enough for roadmap task 5.2.1 while
  leaving room for stronger trackers later.
- Florence-2 can provide boxes and labels, but it should not become the domain
  model for persistence.
- Domain and application tests need deterministic fixtures for track lifecycle
  behaviour.
- Adapter implementations should be swappable without changing BeatCue JSON,
  WebVTT, OpenTimelineIO (OTIO), command-line interface (CLI), or domain
  contracts.
- The v1 product boundary must remain deterministic cue extraction; this ADR
  records a future boundary rather than implementing tracking now.

## Options considered

### Option A: Florence-2-only detections

This option treats Florence-2 object-detection results as sufficient object
signals. It gives useful labels and boxes quickly, but it does not establish
stable track identity, lifecycle state, or minimum persistence. It would force
entry and exit logic either to infer persistence from isolated detections or to
hide tracking state inside an inference adapter.

### Option B: Centroid tracker as the selected implementation

This option makes a centroid-association tracker the object-tracking solution.
It is simple, deterministic, and suitable for early fixtures. The drawback is
that it makes a deliberately limited algorithm sound like the permanent
architecture. It also does not explain how stronger OpenCV, segmentation, or
video-aware trackers can replace it without changing callers.

### Option C: Domain-owned `ObjectTracker` port with a simple default

This option defines object tracking as a domain-owned port. Detector adapters
feed plain observations into a tracker implementation. The first implementation
can be a simple centroid-association default, but the boundary permits later
OpenCV, SAM 2, or remote tracker adapters as long as they return the same
domain values.

| Topic                   | Florence-2 detections | Centroid tracker | Pluggable port |
| ----------------------- | --------------------- | ---------------- | -------------- |
| Track persistence       | Weak                  | Medium           | Strong         |
| First implementation    | Medium                | Strong           | Strong         |
| Future tracker swaps    | Weak                  | Medium           | Strong         |
| Hexagonal boundary      | Medium                | Medium           | Strong         |
| Test fixture stability  | Medium                | Strong           | Strong         |
| Release-scope clarity   | Medium                | Medium           | Strong         |

_Table 1: Object-tracking boundary trade-offs._

## Decision outcome

BeatCue chooses option C. Object tracking is a post-v1 capability behind a
domain-owned `ObjectTracker` port. The port consumes and returns plain domain
values: frame timestamp, source frame identity, bounding box coordinates,
optional label, confidence, stable track ID, track lifecycle, and diagnostics.

The first implementation should use simple centroid association over detector
observations. Florence-2 may feed detector observations with boxes, labels, and
confidence scores, but Florence-2 does not own track identity or lifecycle
state. OpenCV trackers, Segment Anything Model 2 (SAM 2), remote model
services, and advanced video segmentation remain adapter choices for later
roadmap work.

Domain signatures must not expose OpenCV, Transformers, Torch, Pillow, NumPy,
or model-specific objects. Adapters convert those infrastructure values into
domain observations before calling application or domain services.

## Goals and non-goals

Goals:

- Ratify one boundary for later object-tracking implementation.
- Preserve BeatCue's v1 deterministic product scope.
- Separate per-frame detections from cross-frame track persistence.
- Keep tracker protocols and value objects domain-owned.
- Give task 5.2.1 a default implementation path that can be tested with
  deterministic fixtures.

Non-goals:

- Implement production object tracking in this ADR task.
- Add Florence-2, OpenCV, SAM 2, Torch, or remote model dependencies.
- Add CLI flags, BeatCue JSON fields, WebVTT metadata, OTIO metadata, or
  public Python APIs.
- Decide graphics processing unit (GPU) scheduling, remote model credentials,
  or advanced segmentation policy.
- Promote object tracking into the v1 deterministic release.

## Migration plan

1. Signpost this ADR from the technical design, developers' guide, users'
   guide, roadmap, and execution plan.
2. In task 5.2.1, define the `ObjectTracker` protocol and tracking domain
   values in the domain package before adding adapters.
3. Add deterministic unit fixtures for centroid association, including stable
   track IDs, missing detections, edge entry and exit, and confidence handling.
4. Add property tests for track lifecycle invariants, including
   `min_track_persistence_s`, sorted timestamps, empty observation lists, and
   non-finite confidence rejection.
5. Keep detector adapters and tracker adapters outside the domain. Florence-2,
   OpenCV, SAM 2, Torch, Pillow, NumPy, and remote model clients stay
   adapter-internal.
6. Add behavioural and snapshot coverage only when tracking becomes observable
   through the library API, CLI, BeatCue JSON, WebVTT, OTIO, diagnostics, or
   `agent-context`.
7. Use Vidai Mock only for behavioural tests that exercise an
   inference-service adapter. Pure centroid-association tests should not need
   model simulation.

## Known risks and limitations

- Centroid association can fail under occlusion, re-identification, strong
  camera motion, and crowded scenes. The mitigation is to keep it as the
  default behind a replaceable port rather than the only architecture.
- Detector quality affects tracking quality. Florence-2 observations may be
  useful labels and boxes, but task 5.2.1 still has to validate confidence,
  missing detections, and unstable labels.
- Future adapters may need richer diagnostics. Those diagnostics should be
  plain domain values, not wrapped model or framework objects.
- This ADR does not prove the final BeatCue JSON field catalogue for tracks.
  Writer-facing schema changes still require implementation tasks and tests.

## Architectural rationale

This decision follows BeatCue's hexagonal architecture. The domain owns the
`ObjectTracker` port and tracking concepts. Inference libraries, computer
vision libraries, remote services, and hardware scheduling stay in adapters.
Application services depend on the domain port, so later tracker
implementations can change without changing cue classification, writers, or
CLI contracts.

The decision also keeps the release boundary honest. V1 can ship deterministic
cue extraction without object tracking, while later object-entry work can
start from a documented and testable persistence boundary.
