# Architectural decision record (ADR) 007: V1 BeatCue JSON schema

## Status

Accepted (2026-05-10).

BeatCue JSON v1 uses `msgspec.Struct` definitions in the serialization layer as
the stable schema technology for encoding, decoding, and validating lossless
analysis output.

## Date

2026-05-10.

## Context and problem statement

BeatCue JSON is the planned lossless interchange format for `AnalysisResult`.
It carries media metadata, feature summaries, cues, diagnostics, resolved
configuration, provenance, and bounded optional feature series. Later writer
work needs a schema decision before it can produce stable fixtures, round-trip
tests, CLI output, and library-facing contracts.

The domain model remains the canonical application model. It should be
expressed as immutable domain values and domain-owned ports, not as
infrastructure, command-line, or writer-specific structures. The schema
technology therefore has to live at the serialization boundary: it maps domain
values into an explicit JSON shape without making adapters the source of truth.

The technical design already identifies `msgspec.Struct` as the v1 schema
technology. This ADR records the decision so implementation tasks can depend on
one durable source instead of reopening the choice during serializer, fixture,
and snapshot work. The `msgspec` documentation describes the library as a
serialization and validation library with JSON support, typed schemas, `Struct`
types, JSON encode/decode workflows, and no required dependencies.[^1]

## Decision drivers

- Library callers need a typed, documented output contract that can be decoded
  without invoking the CLI.
- CLI users need deterministic machine-readable JSON that remains cleanly
  separated from Rich human output and diagnostics.
- Writer implementation needs round-trip validation through the same schema
  used for encoding.
- Snapshot tests need stable, predictable output shapes, so schema changes are
  intentional and reviewable.
- The schema boundary must preserve BeatCue's hexagonal architecture: domain
  values stay inward-facing, and adapter or framework types stay out of the
  domain.
- V1 output must remain bounded by default; large feature series remain
  opt-in.
- The first implementation should avoid schema generation machinery that would
  slow down the walking skeleton or add another source of truth.

## Options considered

### Option A: `msgspec.Struct` at the serialization boundary

This option defines BeatCue JSON using typed `msgspec.Struct` classes that sit
beside the writer implementation. Domain values are converted into schema
structures for JSON encoding and decoded back through the same structures for
validation.

The option gives implementers concrete Python types, fast JSON support, and a
single round-trip path. It also keeps the schema close enough to the domain
model that reviewers can compare the two without maintaining a separate code
generation pipeline.

### Option B: Dataclasses plus ad hoc JSON dictionaries

This option uses standard dataclasses or domain values and handwritten
dictionary conversion before calling a JSON encoder.

It has a low dependency footprint, but it weakens validation because output
shape depends on conversion code and tests rather than a typed decoding
contract. It also makes round-trip checks easier to skip or accidentally
implement differently from encoding.

### Option C: Pydantic-style models

This option uses a validation model library as the schema layer.

It provides strong validation and familiar ergonomics for many Python users,
but it introduces a larger modelling framework than BeatCue needs for a bounded
writer contract. It also increases the risk that validation model features
become part of the domain model instead of remaining a writer boundary.

### Option D: JSON Schema-first generation

This option writes JSON Schema as the source of truth and generates Python
types or validators from it.

It produces a language-neutral contract, but it adds tooling and ordering
complexity before BeatCue has a working writer. V1 needs a clear Python package
spine and stable snapshots first. A JSON Schema export can be reconsidered once
the runtime schema has proven useful.

| Topic                 | `msgspec.Struct` | Dataclasses and dicts | Pydantic-style models | JSON Schema first |
| --------------------- | ---------------- | --------------------- | --------------------- | ----------------- |
| Library caller types  | Strong           | Medium                | Strong                | Medium            |
| CLI JSON consistency  | Strong           | Medium                | Strong                | Strong            |
| Round-trip validation | Strong           | Weak                  | Strong                | Strong            |
| Snapshot stability    | Strong           | Medium                | Strong                | Strong            |
| Dependency weight     | Low              | Lowest                | Medium                | Medium            |
| Boundary discipline   | Strong           | Medium                | Medium                | Strong            |
| V1 implementation fit | Strong           | Medium                | Medium                | Low               |

_Table 1: Schema technology trade-offs for BeatCue JSON v1._

## Decision outcome

BeatCue chooses option A. BeatCue JSON v1 uses `msgspec.Struct` definitions in
the serialization layer. The domain continues to own `AnalysisResult`, `Cue`,
`TimeRange`, diagnostics, provenance, and related values. Writers map those
immutable domain values into schema structures, encode JSON from those
structures, and validate by decoding JSON back through the same schema.

This decision is suitable for library callers because they get a typed Python
schema that can be imported independently of CLI rendering. It is suitable for
CLI output because the same schema backs file output and machine-readable
standard output. It supports round-trip validation because decoding uses the
declared schema rather than unchecked dictionaries. It supports stable
snapshots because serialized output has one canonical shape that tests can lock
with syrupy and reviewers can inspect when the schema changes.

Replacing `msgspec` requires a later ADR or design update before serializer
implementation continues. A future JSON Schema export may be added if external
tooling needs a language-neutral contract, but JSON Schema is not the v1 source
of truth.

## Goals and non-goals

Goals:

- Ratify one schema technology for BeatCue JSON v1.
- Preserve immutable domain values as the canonical application model.
- Establish the serializer's future testing obligations before writer work
  starts.
- Give roadmap tasks 1.2.1, 2.1.1, and 2.2.1 a stable schema dependency.

Non-goals:

- Implement BeatCue JSON serialization in this ADR task.
- Add or change runtime dependencies in this ADR task.
- Replace domain dataclasses with `msgspec.Struct` types.
- Add CLI commands, writer adapters, or inference-service behaviour.
- Define a complete JSON field catalogue before the domain skeleton and writer
  fixtures exist.

## Migration plan

1. Record this ADR and signpost it from the technical design, users' guide,
   developers' guide, and roadmap.
2. In the later package-skeleton task, keep domain values independent of
   serialization-specific schema structures.
3. In the later BeatCue JSON writer task, implement `msgspec.Struct` schema
   classes at the writer boundary and map from `AnalysisResult`.
4. Add pytest unit tests for domain-to-schema mapping and schema decode
   validation.
5. Add Hypothesis tests for invariants over generated valid and invalid
   results, including cue ordering, cue identifiers, timestamps, diagnostics,
   and bounded feature-series behaviour.
6. Add syrupy snapshots for canonical fixture output and require pull requests
   to explain snapshot changes as schema, formatting, or behaviour changes.
7. Add pytest-bdd scenarios when BeatCue JSON becomes observable through the
   CLI or public library facade.
8. Use Vidai Mock only for later behavioural tests that exercise inference
   services; this schema decision does not introduce inference-service
   behaviour.

## Known risks and limitations

- `msgspec.Struct` may expose constraints that require minor domain-to-schema
  mapping adjustments during writer implementation. The mitigation is to keep
  schema structures at the serialization boundary rather than changing domain
  values to match implementation details.
- The v1 schema may need a language-neutral JSON Schema export later. That
  export should be generated or checked from the accepted runtime schema, not
  introduced as a second source of truth without another decision record.
- Snapshot stability depends on deterministic cue ordering, bounded optional
  series, and stable provenance fields. Serializer work must still implement
  those behaviours explicitly.
- This ADR does not prove the complete field catalogue. It ratifies the schema
  technology so later domain and writer tasks can define the catalogue against
  one selected mechanism.

## Architectural rationale

This decision follows BeatCue's hexagonal architecture. The domain owns the
analysis concepts and invariants. The serialization layer adapts those values
to a JSON contract for library callers, CLI users, and file writers.
`msgspec.Struct` is an adapter-side schema mechanism, not a reason for domain
code to depend on CLI, filesystem, Rich, or other infrastructure concerns.

The decision also keeps the build spine narrow. It closes the schema deferral
without implementing a writer early, so later tasks can add package boundaries,
fixtures, and output tests in the intended order.

______________________________________________________________________

[^1]: `msgspec` documentation, accessed 2026-05-10,
    <https://jcristharif.com/msgspec/>.
