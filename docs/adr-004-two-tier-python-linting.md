# Architectural decision record (ADR) 004: Two-tier Python linting

## Status

Accepted. BeatCue runs Ruff as the first lint tier and a focused Pylint pass
through the PyPy-backed `pylint-pypy-shim` as the second lint tier.

## Date

2026-05-15.

## Context and problem statement

BeatCue needs a lint gate that is fast enough for frequent local use and broad
enough to catch correctness, maintainability, and style issues before review.
The project also needs to stay aligned with the Python lint policy already used
by Episodic, another df12 Python project, so contributors do not have to learn
different rule postures for closely related repositories.

Ruff covers a large share of the desired policy quickly, including import
rules, formatting-adjacent checks, docstrings, annotations, bug patterns,
complexity, pytest conventions, performance hints, and Ruff's Pylint-inspired
rules. Pylint still provides useful checks with different semantics, especially
around logging format strings, match patterns, simplification opportunities,
resource handling, mutation during iteration, and structural complexity.

The open question is how BeatCue should combine those tools without making the
ordinary lint command slow, ambiguous, or dependent on each contributor's local
Python and Pylint installation.

## Decision drivers

- `make lint` must remain the single documented lint command.
- Ruff should run first because it is fast and catches the broadest set of
  issues with low feedback latency.
- Pylint should run as a focused second tier rather than as an unbounded
  default ruleset.
- The Pylint execution path must be reproducible, including the shim revision.
- BeatCue should inherit the Episodic lint policy unless there is a documented
  local reason to diverge.
- The lint gate must work from the project Makefile instead of relying on
  undocumented shell snippets.

## Options considered

### Option A: Ruff only

This option keeps `make lint` as a single Ruff invocation.

It is fast and simple, but it loses Pylint checks that still add value for
logging, pattern matching, simplification, resource handling, mutation during
iteration, and design limits. It also diverges from the Episodic lint
architecture.

### Option B: Ruff plus system Pylint

This option runs Ruff first and then runs whatever `pylint` binary is available
on the contributor's path or in the project virtual environment.

It adds the second tier, but the result depends on local interpreter and
package state. That weakens reproducibility and makes review failures harder to
diagnose.

### Option C: Ruff plus pinned PyPy Pylint shim

This option runs Ruff from the project virtual environment and then invokes a
pinned `pylint-pypy-shim` revision through `uv tool run --python pypy`.

It keeps the fast Ruff pass first, adds the selected Pylint coverage, and pins
the shim source used to execute Pylint. The Makefile exposes variables for
diagnostics while keeping the default path reproducible.

| Topic            | Ruff only | Ruff plus system Pylint | Ruff plus PyPy shim |
| ---------------- | --------- | ----------------------- | ------------------- |
| Local speed      | Strong    | Medium                  | Medium              |
| Rule coverage    | Medium    | Strong                  | Strong              |
| Reproducibility  | Strong    | Weak                    | Strong              |
| Episodic parity  | Weak      | Medium                  | Strong              |
| Makefile clarity | Strong    | Medium                  | Strong              |

_Table 1: Lint architecture trade-offs._

## Decision outcome

BeatCue chooses option C. The `lint` target builds the project environment,
runs `ruff check`, and then runs Pylint through the pinned `pylint-pypy-shim`
tool against `beatcue` and `tests`.

The Pylint pass disables all messages by default and enables a curated message
set imported from Episodic. Ruff remains responsible for the broad lint
baseline, including the shared target Python version, import policy, docstring
style, banned deprecated `typing.*` APIs, annotation checks, and local
complexity thresholds.

The Makefile variables `PYLINT_PYTHON`, `PYLINT_TARGETS`,
`PYLINT_PYPY_SHIM_REF`, `PYLINT_PYPY_SHIM`, and `PYLINT` document how the
second tier is assembled. Overrides are for toolchain diagnosis, not for
routine pull-request validation.

## Goals and non-goals

Goals:

- Provide one documented lint command for contributors.
- Keep Ruff as the first and fastest lint tier.
- Add selected Pylint checks without adopting Pylint's full default policy.
- Share the Episodic Python lint posture where it fits BeatCue.
- Pin the PyPy shim revision used to run Pylint.

Non-goals:

- Replace Ruff formatting or `make check-fmt`.
- Require contributors to install a project-local Pylint package manually.
- Treat the entire Episodic repository as BeatCue's configuration source of
  truth.
- Add continuous integration behaviour in this ADR.

## Migration plan

1. Import Episodic's Ruff policy into `pyproject.toml`.
2. Add the focused Pylint configuration to `pyproject.toml`.
3. Update the Makefile so `make lint` runs Ruff first and the shimmed Pylint
   tier second.
4. Document the linting architecture, Makefile variables, and configuration
   entrypoints in the developers' guide.
5. Revisit the policy when Episodic changes its lint baseline, and record any
   deliberate BeatCue divergence in the relevant pull request.

## Known risks and limitations

- Managed PyPy may lag the project's target Python version. The Pylint
  configuration disables `syntax-error` so the second tier remains useful on
  files it can parse while Ruff and the project type checker continue to cover
  the Python target.
- The second lint tier is slower than Ruff alone. Running Ruff first preserves
  fast failure for the common case.
- The policy inherits Episodic's assumptions. BeatCue may need documented local
  exceptions as the package grows into media adapters, command execution,
  inference services, and CLI surfaces.
- The shim pin must be advanced intentionally when upstream shim behaviour or
  Pylint compatibility changes.

## Architectural rationale

The decision keeps linting as a build concern rather than an application
dependency. It supports BeatCue's hexagonal architecture indirectly by making
complexity, import discipline, logging behaviour, and resource handling visible
before code review. It also keeps the contributor workflow simple: the Makefile
owns tool execution, while `pyproject.toml` owns rule configuration.
