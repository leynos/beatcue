# Architectural decision record (ADR) 002: V1 port surface

## Status

Accepted. BeatCue keeps the twelve named ports as the long-term boundary, but
classifies them by v1 requirement so implementation does not build post-v1
adapters early.

## Date

2026-05-09.

## Context and problem statement

The technical design lists twelve driven ports. The Logisphere review noted
that this surface may be too broad for v1 and that some ports exist for future
substitutability rather than immediate implementation needs.

BeatCue also needs a strict hexagonal boundary before implementation starts. If
ports are removed entirely, post-v1 model and object work may leak
infrastructure types into the domain later. If every port is treated as v1
implementation work, the first release becomes too large.

## Decision drivers

- V1 must remain a deterministic, local-only product.
- The domain must not import adapter or model libraries.
- Implementers need to know which ports are required now and which are future
  seams.
- Test fakes should use the same contracts as real adapters.
- Constructor arity should be monitored, but dependency grouping should not
  hide real pipeline dependencies prematurely.

## Options considered

### Option A: Reduce the design to only current v1 ports

This narrows immediate scope, but future semantic and object work would need to
reopen the architecture and may be tempted to bypass the domain boundary.

### Option B: Treat all twelve ports as v1 implementation work

This preserves the full boundary, but it makes v1 too broad and delays the
walking skeleton and deterministic analysis loop.

### Option C: Keep twelve ports and classify implementation timing

This preserves the long-term boundary while making v1 scope explicit. Required
ports are implemented for v1. Post-v1 ports remain design boundaries and test
contracts, but their concrete adapters wait until enrichment work starts.

| Topic               | Only v1 ports | All ports in v1 | Classified ports |
| ------------------- | ------------- | --------------- | ---------------- |
| V1 delivery scope   | Small         | Large           | Bounded          |
| Future boundary     | Weak          | Strong          | Strong           |
| Implementation risk | Medium        | High            | Low              |
| Review clarity      | Medium        | Low             | High             |

_Table 1: Port-surface options._

## Decision outcome

BeatCue chooses option C. The technical design marks each port as `Required` or
`Post-v1`. V1 implementation must prioritize required deterministic,
configuration, writer, job, profile, and command ports. `ObjectTracker` and
`SemanticAnnotator` remain post-v1 ports until enrichment work begins.

The `AnalyseVideo` constructor may be verbose during v1. Group injected
dependencies only after implementation shows repeated wiring pain. Acceptable
future groups include a media-inputs bundle or writer bundle, but those groups
must still contain explicit port implementations and must not permit adapters
to call one another directly.

## Known risks and limitations

- Keeping post-v1 ports in the design may still make the architecture look
  larger than the first implementation.
- Required ports may need further splitting if adapters grow beyond one
  responsibility.
- Grouping dependencies later must preserve testability and explicit
  composition-root wiring.
