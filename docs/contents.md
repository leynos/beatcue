# Documentation contents

This document indexes the BeatCue documentation set and points readers to the
right source of truth for use, maintenance, design, and planning work.

## Index

- [Documentation contents](contents.md) - This index of repository
  documentation.
- [Users' guide](users-guide.md) - User-facing behaviour, expected workflows,
  and public-facing guarantees as BeatCue grows.
- [Developers' guide](developers-guide.md) - Maintainer workflows, development
  commands, and implementation practices.
- [Repository layout](repository-layout.md) - The purpose and ownership
  boundary of the main repository paths.
- [Documentation style guide](documentation-style-guide.md) - Writing,
  Markdown, roadmap, Architecture Decision Record (ADR), and Request for
  Comments (RFC) conventions for repository documentation.
- [Scripting standards](scripting-standards.md) - Standards for robust helper
  scripts, command execution, and command mocking.

## Design and review

- [BeatCue technical design](beatcue-technical-design.md) - The main system
  design, architecture, contracts, and planned evolution.
- [BeatCue Logisphere design stage review](beatcue-logisphere-design-stage-review.md)
  - Multi-perspective review notes for the design stage.
- [Complexity antipatterns and refactoring strategies](complexity-antipatterns-and-refactoring-strategies.md)
  - Refactoring guidance and complexity patterns relevant to the codebase.

## Decision records

- [ADR 001: Colourgram domain boundary](adr-001-colourgram-domain-boundary.md)
  - Accepted boundary decision for colourgram domain ownership.
- [ADR 002: V1 port surface](adr-002-v1-port-surface.md) - Accepted v1 port
  surface and integration boundary.
- [ADR 003: Hexagonal architecture enforcement](adr-003-hexagonal-architecture-enforcement.md)
  - Architecture enforcement policy for the Python package.
- [ADR 004: Two-tier Python linting](adr-004-two-tier-python-linting.md) -
  Python linting policy and rationale.
- [ADR 005: Hecate architecture enforcement](adr-005-hecate-architecture-enforcement.md)
  - Hecate-based enforcement decision for architecture boundaries.
- [ADR 006: V1 local-only model and privacy policy](adr-006-v1-local-only-model-and-privacy-policy.md)
  - Accepted local-only model and privacy decision.
- [ADR 007: V1 BeatCue JSON schema](adr-007-v1-beatcue-json-schema.md) -
  Accepted v1 BeatCue JSON schema decision.
- [ADR 008: V1 object tracking boundary](adr-008-v1-object-tracking-boundary.md)
  - Accepted object tracking ownership and extension boundary.

## Plans

- [Roadmap](roadmap.md) - Current delivery sequence and task breakdown.
- [Execution plans](execplans/) - Branch-level implementation plans for
  non-trivial workstreams.
  - [Record v1 schema decision for BeatCue JSON](execplans/1-1-1-record-v1-schema-decision-for-beat-cue-json.md)
    - Plan for the v1 JSON schema decision record.
  - [Record v1 object tracking boundary](execplans/1-1-2-record-v1-object-tracking-boundary.md)
    - Plan for the object tracking boundary decision record.
  - [Record local-only policy for v1](execplans/1-1-3-record-local-only-policy-for-v1.md)
    - Plan for the local-only model and privacy decision.
  - [Create package skeleton](execplans/1-2-1-create-package-skeleton.md) -
    Plan for the initial package skeleton.
  - [Adopt Hecate](execplans/adopt-hecate.md) - Plan for adopting Hecate
    architecture enforcement.
  - [Import hex architecture enforcement](execplans/import-hex-architecture-enforcement.md)
    - Plan for importing hexagonal architecture enforcement guidance.
  - [Resolve BeatCue Logisphere design stage review](execplans/resolve-beatcue-logisphere-design-stage-review.md)
    - Plan for resolving design-stage review findings.
