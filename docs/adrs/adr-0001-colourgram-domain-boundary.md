# Architectural decision record (ADR) 001: Colourgram domain boundary

## Status

Accepted. BeatCue treats the colourgram as a domain-facing feature series, not
as an adapter-owned image-processing artefact.

## Date

2026-05-09.

## Context and problem statement

The technical design uses colour features to detect cuts, fades, flashes, scene
changes, and action-intensity changes. The Logisphere review asked whether the
colourgram belongs in the domain model or remains internal to the frame and
computer-vision adapters.

The boundary matters because domain services must not import OpenCV, NumPy, or
adapter-specific frame types. At the same time, cue classification needs a
stable representation of visual features so tests and writers can explain why a
cue exists.

## Decision drivers

- Domain services need deterministic visual feature values for classification.
- Adapters must be free to change OpenCV, PySceneDetect, or frame-sampling
  internals without changing cue rules.
- BeatCue JSON should explain cues with bounded summaries, not raw frame data.
- The design must preserve the hexagonal rule that infrastructure types do not
  leak into domain code.

## Options considered

### Option A: Keep colourgram entirely adapter-internal

The adapter would compute visual events and return only cue candidates or
summary values.

This keeps the domain smaller, but it hides the feature series that action
intensity and cue fusion need to reason about.

### Option B: Make raw colourgram arrays domain values

The domain would own full colourgram arrays, probably backed by NumPy-like
structures.

This gives domain services direct access to visual data, but it risks pulling
heavy infrastructure types into the domain and makes BeatCue JSON unbounded by
default.

### Option C: Make bounded colourgram feature series domain-facing

Adapters convert raw frames into domain-owned feature series and summaries. Raw
frame buffers, OpenCV matrices, and NumPy arrays remain adapter-internal.

| Topic                 | Adapter-internal only | Raw domain arrays | Bounded domain feature series |
| --------------------- | --------------------- | ----------------- | ----------------------------- |
| Domain explainability | Low                   | High              | High                          |
| Adapter isolation     | High                  | Low               | High                          |
| Memory control        | High                  | Low               | High                          |
| Testability           | Medium                | Medium            | High                          |

_Table 1: Colourgram boundary options._

## Decision outcome

BeatCue chooses option C. `Colourgram` in user-facing terminology refers to the
conceptual visual feature series. The domain-facing implementation should use a
bounded value such as `VisualFeatureSeries` or `ColourgramSeries` containing
timestamps and scalar feature vectors. Raw frame data and computer-vision
library types remain inside adapters.

The default `AnalysisResult` stores aggregate feature summaries. Full
frame-level series are present only when `include_series` is enabled and the
configured series cap is not exceeded.

## Known risks and limitations

- The domain value must stay compact enough for default memory bounds.
- Feature names and units must be stable once snapshots exist.
- If future detectors require richer image data, they need a new adapter port
  rather than expanding the colourgram value into raw image storage.
