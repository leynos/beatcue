# Architectural decision record (ADR) 009: dependency extras and Python 3.14 markers

## Status

Accepted (2026-06-14). BeatCue declares runtime dependency extras for the
designed capability groups, uses development dependency groups for tooling, and
marker-gates optional packages that do not resolve cleanly on Python 3.14.

## Date

2026-06-14.

## Context and problem statement

BeatCue targets Python 3.14 and uses `uv` for local development. The technical
design defines five dependency groups: `core`, `media`, `editorial`, `models`,
and `dev`. Contributors need a fresh checkout to run `uv sync --group dev` and
then `make all` without hand-installing tooling.

Some optional packages named by the design are not yet reliable on Python 3.14.
`librosa` is blocked by its numba and llvmlite stack, OpenTimelineIO lacks a
Python 3.14 wheel, and the post-v1 model stack depends on Torch wheel
availability. Declaring those dependencies unconditionally would make `uv lock`
fail even though the corresponding capabilities are optional or post-v1.

## Decision outcome

Runtime capability groups live in `[project.optional-dependencies]`.
Development-only tooling lives in `[dependency-groups].dev`.

BeatCue declares:

- `core` for Cyclopts, Rich, Cuprum, and msgspec;
- `media` for the headless OpenCV stack, PySceneDetect, and librosa;
- `editorial` for OpenTimelineIO;
- `models` for local-only post-v1 model adapters;
- `dev` for pytest, pytest-bdd, syrupy, Hypothesis, CmdMox, Hecate, Ruff,
  Pyright, Pylint support, and related test tooling.

Packages known not to resolve cleanly on Python 3.14 are guarded with
`python_full_version < '3.14'` markers until upstream support lands. This keeps
the design contract visible while allowing `uv lock`, `uv sync --group dev`,
and `make all` to succeed on the supported interpreter.

BeatCue uses `opencv-python-headless` and `scenedetect-headless`, not the GUI
OpenCV or bare PySceneDetect distributions. Both expose the same import
namespaces as their GUI-capable variants, so Hecate tracks import names such as
`cv2` and `scenedetect`, not distribution names.

## Consequences

Contributors can sync the development environment without installing the
post-v1 editorial or model stacks. Capability checks in future adapters must
still fail clearly when a user requests unavailable optional functionality.

The marker-gated declarations are temporary. Remove the markers when upstream
packages publish reliable Python 3.14-compatible releases and the lockfile can
resolve without local build failures.

Architecture policy must use importable module names. For example, the
`cmd-mox` distribution imports as `cmd_mox`, so Hecate must allow or reject
`cmd_mox`, not `cmdmox`.

## Non-goals

- Implement media, editorial, model, CLI, writer, or configuration adapters.
- Downgrade BeatCue's Python requirement to satisfy optional packages.
- Add remote model execution.
  [ADR 006](adr-006-v1-local-only-model-and-privacy-policy.md) remains the
  controlling local-only model policy.
