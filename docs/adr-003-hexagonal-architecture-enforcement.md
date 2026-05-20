# Architectural decision record (ADR) 003: Hexagonal architecture enforcement

## Status

Superseded on 2026-05-20 by
[ADR 005: Hecate architecture enforcement](adr-005-hecate-architecture-enforcement.md).
 BeatCue now enforces its documented package dependency direction with Hecate
rather than the repository-local Python checker described here.

## Date

2026-05-11.

## Context and problem statement

BeatCue is still a skeleton package, but its design already defines strict
hexagonal boundaries. Domain code must remain pure, application services must
orchestrate through domain-owned ports, adapters may contain infrastructure, and
 `beatcue.config` is the narrow composition root that wires concrete
dependencies.

Ordinary unit tests are not enough to preserve those boundaries while the
package tree grows. A future import from `beatcue.domain` to
`beatcue.adapters.outbound`, or from `beatcue.application` directly to an
OpenCV-backed adapter, could compile and still violate the design. Package
barrels such as `__init__.py` files can also hide those dependencies through
explicit or star re-exports.

## Decision drivers

- Keep BeatCue's domain and application code free of infrastructure imports.
- Make architecture drift visible in the local quality gate.
- Preserve the documented `beatcue.config` composition-root exception without
  broadening application or domain permissions.
- Avoid adding a runtime dependency for an internal fitness function.
- Trial the Episodic checker mechanism before extracting a shared tool.

## Decision outcome / proposed direction

BeatCue will keep a local checker in `beatcue.architecture` and expose it
through:

```bash
python -m beatcue.architecture
make check-architecture
make lint
```

The checker parses Python modules with the standard-library `ast` module,
collects syntactic imports, expands package `__init__.py` re-exports including
star re-exports, classifies modules into BeatCue architecture groups, and
reports `ARCH001` when an importer depends on a forbidden group.

The default production policy is BeatCue-specific:

| Group              | Package prefixes                                        | Allowed imports                                             |
| ------------------ | ------------------------------------------------------- | ----------------------------------------------------------- |
| `composition_root` | `beatcue.config`                                        | all BeatCue architecture groups and infrastructure          |
| `domain`           | `beatcue.domain`                                        | `domain`                                                    |
| `application`      | `beatcue.application`                                   | `domain`, `application`                                     |
| `inbound_adapter`  | `beatcue.cli`, `beatcue.adapters.inbound`               | `domain`, `application`, `inbound_adapter`                  |
| `outbound_adapter` | `beatcue.adapters.outbound`                             | `domain`, `application`, `outbound_adapter`                 |
| `adapter`          | `beatcue.adapters`                                      | `domain`, `application`, adapter groups, and infrastructure |
| `infrastructure`   | `rich`, `cyclopts`, `cv2`, `librosa`, and related tools | none as an importer; allowed only where policy permits it   |

_Table 1: BeatCue architecture groups enforced by the checker._

The current production package has too little future-shape code to exercise all
rules, so tests use small fixture packages under
`tests/fixtures/architecture/`. Those fixtures prove the intended future
boundaries without introducing placeholder domain, application, or adapter
implementations into the real package.

## Goals and non-goals

- Goals:
  - Fail fast when domain or application code imports adapters or
    infrastructure.
  - Allow `beatcue.config` to wire application services to concrete adapters.
  - Detect forbidden dependencies hidden behind package-barrel re-exports.
  - Include the architecture check in `make lint`.
- Non-goals:
  - Replace general linting, type checking, or behavioural tests.
  - Implement BeatCue's future domain, application, or adapter modules.
  - Extract a shared df12 architecture-checking package in this change.
  - Add Import Linter, Semgrep, Astroid, or another dependency in this trial.

## Known risks and limitations

The checker is static and syntactic. It does not execute imports, inspect
runtime plugin loading, or infer dynamically constructed module names. That is
intentional for this trial: BeatCue's architecture rule is about visible source
imports.

The policy is currently Python code rather than TOML or JSON. That keeps the
mechanism small and explicit, but a shared tool should probably offer a
configuration file before it is reused across more df12 projects.

The fixture strategy proves future boundaries before production modules exist,
but it cannot prove the future production layout until those packages are
implemented. `make check-architecture` still checks the current real `beatcue/`
tree on every lint run.

## Architectural rationale

Hexagonal architecture protects the domain model by making infrastructure a
replaceable implementation detail. Enforcing import direction in the local
quality gate turns that design rule into an executable constraint. Keeping the
composition root explicit preserves the practical place where concrete adapters
are allowed to meet application services.
