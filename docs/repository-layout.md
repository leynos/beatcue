# Repository layout

This document describes the main BeatCue repository paths and the role each
path plays. It is the canonical location for repository-layout guidance.

## Top-level structure

The tree below is an orientation sketch of the important paths, not an
exhaustive listing of every file.

```plaintext
.
|-- .github/
|-- .rules/
|-- beatcue/
|   |-- adapters/
|   |-- application/
|   |-- config/
|   `-- domain/
|-- docs/
|   `-- execplans/
|-- tests/
|   |-- features/
|   `-- fixtures/
|-- AGENTS.md
|-- Makefile
|-- README.md
|-- pyproject.toml
`-- uv.lock
```

## Path responsibilities

### `.github/`

Project automation lives here. The current repository uses this path for
Dependabot configuration.

### `.rules/`

Python development rules live here. Read these documents before changing Python
style, typing, error handling, context manager, generator, return, or packaging
conventions.

### `beatcue/`

Application and library source code lives here. The package follows a hexagonal
architecture:

- `beatcue/domain/` owns domain concepts and must remain independent of
  adapters and infrastructure.
- `beatcue/application/` coordinates use cases and may depend on the domain.
- `beatcue/adapters/` contains inbound and outbound adapter code around the
  application boundary.
- `beatcue/config/` is the composition-root area for wiring configuration and
  dependencies.

### `docs/`

Long-lived project documentation lives here. Use
[documentation contents](contents.md) as the index, and keep design decisions
in the technical design or Architecture Decision Records (ADRs) rather than
only in code comments.

### `docs/execplans/`

Execution plans for non-trivial implementation work live here. Each plan should
be named after the branch or workstream and kept current while the work is in
progress.

### `tests/`

Automated tests live here. Unit and architecture tests sit at the top level of
`tests/`, behaviour specifications live under `tests/features/`, and shared
test data or support files live under `tests/fixtures/`.

### Root configuration files

- `AGENTS.md` defines local agent and contributor workflow rules.
- `Makefile` exposes the preferred quality gates and development commands.
- `README.md` introduces the project for repository visitors.
- `pyproject.toml` defines package metadata, dependencies, and tool
  configuration.
- `uv.lock` records the resolved Python dependency environment.
