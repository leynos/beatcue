# Architectural decision record (ADR) 005: Hecate architecture enforcement

## Status

Accepted on 2026-05-20. BeatCue enforces its documented package dependency
direction with Hecate configured in `pyproject.toml` and run through the
existing Makefile gate.

## Date

2026-05-20.

## Context and problem statement

ADR 003 established a repository-local architecture checker in
`beatcue.architecture`. That checker proved BeatCue's hexagonal dependency rule
before the real domain, application, and adapter packages existed. It also made
package-barrel re-exports visible to the local quality gate.

The local checker had become maintenance surface that duplicated Hecate, a
shared df12 architecture-checking package. BeatCue needs the same boundary
enforcement, but it should not keep local import parsing, re-export indexing,
policy classification, and command-line behaviour after Hecate can provide
those concerns from a pinned upstream source.

## Decision drivers

- Keep `make check-architecture` and `make lint` as stable contributor
  commands.
- Preserve BeatCue's `ARCH001` diagnostic identifier.
- Keep architecture policy declarative and reviewable in `pyproject.toml`.
- Avoid retaining two architecture checkers with overlapping semantics.
- Keep fixture coverage for BeatCue-specific policy examples.

## Decision outcome / proposed direction

BeatCue uses Hecate pinned to commit
`46f8c8798e7a80a3a1ab5a13c2a000a4423ffc12`. The package is installed as a
development dependency, and `[tool.hecate]` in `pyproject.toml` declares the
ordered architecture groups.

The Makefile target remains the stable entry point:

```bash
make check-architecture
make lint
```

`make check-architecture` runs:

```bash
$(UV_ENV) $(UV) run hecate check
```

The Hecate policy keeps the same high-level groups as the local checker:

- `composition_root` for `beatcue.config`;
- `domain` for `beatcue.domain`;
- `application` for `beatcue.application`;
- `inbound_adapter` for `beatcue.cli` and `beatcue.adapters.inbound`;
- `outbound_adapter` for `beatcue.adapters.outbound`;
- `adapter` for broader `beatcue.adapters` modules;
- `infrastructure` for external packages such as `cyclopts`, `rich`, `cv2`,
  `librosa`, `transformers`, `cuprum`, and `cmdmox`.

Hecate is configured with `include_external_packages = true` and
`default_rule_id = "ARCH001"` so BeatCue can continue rejecting direct
infrastructure imports with the established diagnostic identifier.

## Goals and non-goals

- Goals:
  - Enforce the same inward dependency direction through a shared tool.
  - Keep contributor commands stable.
  - Keep BeatCue-specific fixture tests for the policy shape.
  - Remove the repository-local checker implementation.
- Non-goals:
  - Change BeatCue's future media-analysis library API.
  - Change the planned user-facing video-analysis CLI.
  - Reimplement Hecate parser, re-export, or configuration tests in BeatCue.

## Known risks and limitations

Hecate diagnostics are not byte-for-byte identical to the removed local
checker. For the star re-export fixture, Hecate reports the forbidden adapter
barrel and public symbol as an `application -> adapter` violation, rather than
naming the outbound origin in the text diagnostic. This still fails the gate
for the hidden adapter dependency.

Hecate is pinned by Git commit because the public package name may collide with
unrelated historical packages. Dependency updates must deliberately change the
Git revision in `pyproject.toml` and `uv.lock`.

## Architectural rationale

The architecture rule belongs to BeatCue, but import parsing and re-export
analysis do not. Moving those mechanics to Hecate keeps the boundary
enforcement explicit while reducing local maintenance. Keeping the Makefile
entry point stable preserves developer workflow and lets future implementation
work rely on the same quality gate.
