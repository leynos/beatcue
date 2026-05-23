# Replace BeatCue's local architecture checker with Hecate

This ExecPlan (execution plan) is a living document. The sections `Constraints`,
 `Tolerances`, `Risks`, `Progress`, `Surprises & Discoveries`, `Decision log`,
and `Outcomes & retrospective` must be kept up to date as work proceeds.

Status: COMPLETE

This plan was approved for implementation on 2026-05-20. Keep this document
current as the migration proceeds, and do not mark roadmap work complete until
the replacement has been implemented and validated.

## Purpose / big picture

BeatCue currently enforces its hexagonal architecture with repository-local
Python code in `beatcue/architecture/`. That checker proved the intended
dependency direction early, but its import parser, policy model, command-line
interface (CLI), re-export expansion, tests, and documentation are now local
maintenance surfaces that Hecate already provides as a reusable package.

After this plan is approved and implemented, `make check-architecture` and
`make lint` will enforce the same BeatCue boundaries through Hecate pinned to
`https://github.com/leynos/hecate` at commit
`46f8c8798e7a80a3a1ab5a13c2a000a4423ffc12`. Contributors will keep using the
Makefile gates they already know, while the architecture policy itself will
live as declarative TOML configuration under `[tool.hecate]` in
`pyproject.toml`.

Observable success is concrete:

- `make check-architecture` runs Hecate and exits `0` on the current package.
- A deliberate forbidden import from a domain fixture to an adapter still fails
  with a deterministic architecture diagnostic.
- `make lint` still runs the architecture check after Ruff and Pylint.
- `make check-fmt`, `make lint`, and `make test` all pass.
- CodeRabbit review reports no unresolved concerns for the migration.
- Documentation explains Hecate as the active architecture gate.
- The relevant roadmap entry is marked done only after the replacement is
  implemented and validated, not while this draft plan is merely written.

## Constraints

This plan is for planning only until explicit approval. Implementation must not
begin from the draft phase.

The implementation must preserve BeatCue's hexagonal dependency rule from
`docs/beatcue-technical-design.md` section 5: domain code imports only domain
code and standard-library code; application code imports application and domain
code; adapters hold infrastructure dependencies; `beatcue.config` remains the
composition root that may wire application services to concrete adapters.

The public contributor workflow must remain stable. `make check-architecture`
and `make lint` continue to be the documented entry points, even if the command
inside the Makefile changes from `python -m beatcue.architecture` to
`hecate check`.

Hecate must be pinned to commit `46f8c8798e7a80a3a1ab5a13c2a000a4423ffc12`. If
the package cannot be installed from that Git commit through `uv`, the
implementation stops and records the installation failure in the Decision Log.

Do not keep both enforcement engines active long term. A short parity phase is
allowed while tests are being migrated, but the final state must have Hecate as
the single architecture checker used by `make check-architecture`.

Do not loosen architecture policy to make the migration pass. Any Hecate
configuration that allows a previously forbidden domain-to-adapter,
application-to-adapter, or direct infrastructure import is a failed migration.

Documentation must stay aligned with the code. Update
`docs/adr-003-hexagonal-architecture-enforcement.md` or create a superseding
ADR if the decision is substantive; update `docs/beatcue-technical-design.md`,
`docs/developers-guide.md`, and `docs/users-guide.md` where they describe
behaviour, contributor practice, or CLI/library-visible effects.

Use the requested and relevant skills when executing this plan:

- `leta`, for symbol navigation and reference checks before editing code;
- `hexagonal-architecture`, for validating the boundary model;
- `execplans`, for keeping this living plan current;
- `commit-message`, for file-based Git commit messages.

Quality gates must use Makefile targets and tee logs under `/tmp`, for example
`/tmp/check-fmt-beatcue-feat-plan-hecate-adoption.out`. Do not run format
checks, linters, or tests in parallel.

## Tolerances

Implementation must stop and ask for direction if any of these thresholds are
reached:

- Scope: more than 18 repository files or more than 900 net lines would need to
  change.
- Interface: any BeatCue public library API, future user-facing CLI contract,
  or documented Makefile target would need to be removed or renamed.
- Dependency: Hecate requires any dependency other than its pinned Git package
  and the dependencies already declared by that package.
- Behaviour: Hecate cannot express the current ordered groups, composition-root
  exception, external infrastructure grouping, or re-export expansion.
- Diagnostics: tests or documentation require preserving exact `ARCH001` text,
  but Hecate can only emit `HEC001` without an equivalent
  `default_rule_id = "ARCH001"` configuration.
- Parity: more than one existing forbidden fixture becomes allowed, or any
  existing allowed fixture becomes forbidden, after the TOML policy is applied.
- Gates: the same gate still fails after three focused fix attempts.
- Review: `coderabbit review --agent` reports a concern whose fix would exceed
  these tolerances.
- Ambiguity: two valid migration paths would produce materially different
  contributor workflows or policy semantics.

## Risks

Risk: Hecate identity or install source is confused with an unrelated package
of the same name. Severity: high. Likelihood: medium. Mitigation: install
Hecate from the Git URL and exact commit, never from an unpinned package name
alone. Record the raw documentation sources and the installed package metadata
in the implementation evidence.

Risk: Hecate's policy language almost, but not exactly, matches BeatCue's local
checker. Severity: high. Likelihood: medium. Mitigation: translate the current
groups from `beatcue/architecture/policy.py` into `[tool.hecate]`, then run
parity checks against the existing fixture packages before deleting local
checker code.

Risk: Re-export handling regresses and package barrels hide forbidden imports.
Severity: high. Likelihood: low. Mitigation: keep or rewrite BeatCue-level
tests that prove a forbidden adapter import through
`from beatcue.adapters import db` and star exports remains visible to Hecate.

Risk: The migration creates noisy diagnostic churn for existing documentation
and tests. Severity: medium. Likelihood: medium. Mitigation: set
`default_rule_id = "ARCH001"` in `[tool.hecate]` unless a deliberate ADR
records a move to `HEC001`. Prefer preserving the Makefile contract over
preserving the removed local Python API.

Risk: Removing `beatcue.architecture` breaks tests that were really testing
Hecate internals rather than BeatCue policy. Severity: medium. Likelihood:
high. Mitigation: move generic checker coverage to the Hecate project by
relying on the pinned Hecate tests and keep only BeatCue policy, fixture,
Makefile, and documentation coverage in this repository.

Risk: Documentation overstates user-visible functionality. Severity: medium.
Likelihood: medium. Mitigation: keep `docs/users-guide.md` limited to real
BeatCue behaviour and link the architecture gate as contributor or library
packaging behaviour, not as an end-user media-analysis command.

## Current state

The active local checker lives under `beatcue/architecture/`:

- `beatcue/architecture/__main__.py` calls the CLI entry point.
- `beatcue/architecture/cli.py` supports `--package`, `--root`, and
  `--fixture-policy`.
- `beatcue/architecture/checker.py` scans Python files, builds re-export
  indexes, classifies imports, and reports violations.
- `beatcue/architecture/policy.py` defines ordered groups and the default
  BeatCue policy.
- `beatcue/architecture/reexports.py` resolves package-barrel exports,
  `__all__`, public fallback symbols, and statically resolvable star exports.
- `beatcue/architecture/_imports.py` contains module-name and relative-import
  helpers.

The current Makefile target is:

```makefile
check-architecture: .deps ## Verify hexagonal import boundaries
 $(call ensure_uv)
 $(UV_ENV) $(UV) run python -m beatcue.architecture
```

`make lint` runs Ruff, Pylint, and then `$(MAKE) check-architecture`.

The current tests are:

- `tests/test_architecture_checker.py`, for policy and fixture behaviour;
- `tests/test_architecture_cli.py`, for the local CLI and module entry point;
- `tests/test_architecture_reexports.py`, for re-export resolution;
- `tests/fixtures/architecture/`, for future-shape boundary examples.

The relevant documentation is:

- `docs/adr-003-hexagonal-architecture-enforcement.md`, which currently
  accepts the local checker decision;
- `docs/beatcue-technical-design.md`, especially section 5 on architecture and
  section 17 on verification;
- `docs/developers-guide.md`, especially "Architectural rules" and "Quality
  gates";
- `docs/users-guide.md`, for any real user-facing behaviour;
- `docs/roadmap.md`, where task 1.2.2 records the existing architecture
  fitness function as complete.

## Hecate reference

Use these Hecate documents as the migration source of truth at commit
`46f8c8798e7a80a3a1ab5a13c2a000a4423ffc12`:

- <https://raw.githubusercontent.com/leynos/hecate/46f8c8798e7a80a3a1ab5a13c2a000a4423ffc12/docs/users-guide.md>
- <https://raw.githubusercontent.com/leynos/hecate/46f8c8798e7a80a3a1ab5a13c2a000a4423ffc12/docs/migration-beatcue.md>
- <https://raw.githubusercontent.com/leynos/hecate/46f8c8798e7a80a3a1ab5a13c2a000a4423ffc12/docs/configuration.md>

The Hecate user guide says `hecate check` discovers `[tool.hecate]` in
`pyproject.toml`, supports `--config`, supports `--format json`, emits
deterministic text diagnostics, exits `0` for success, exits `1` for
architecture violations, and exits `2` for configuration, command-line, or
package-root validation failures.

The Hecate BeatCue migration notes translate the local policy into ordered TOML
groups. The implementation should start from this shape and then verify it
against the current repository:

```toml
[tool.hecate]
root_packages = ["beatcue"]
include_external_packages = true
default_rule_id = "ARCH001"

[[tool.hecate.groups]]
name = "composition_root"
prefixes = ["beatcue.config"]
allowed = [
  "adapter",
  "application",
  "composition_root",
  "domain",
  "inbound_adapter",
  "infrastructure",
  "outbound_adapter",
]

[[tool.hecate.groups]]
name = "domain"
prefixes = ["beatcue.domain"]
allowed = ["domain"]

[[tool.hecate.groups]]
name = "application"
prefixes = ["beatcue.application"]
allowed = ["application", "domain"]

[[tool.hecate.groups]]
name = "inbound_adapter"
prefixes = ["beatcue.cli", "beatcue.adapters.inbound"]
allowed = ["inbound_adapter", "composition_root", "application", "domain"]

[[tool.hecate.groups]]
name = "outbound_adapter"
prefixes = ["beatcue.adapters.outbound"]
allowed = [
  "outbound_adapter",
  "adapter",
  "application",
  "domain",
  "infrastructure",
]

[[tool.hecate.groups]]
name = "adapter"
prefixes = ["beatcue.adapters"]
allowed = [
  "adapter",
  "application",
  "domain",
  "infrastructure",
  "outbound_adapter",
]

[[tool.hecate.groups]]
name = "infrastructure"
prefixes = ["cmdmox", "cuprum", "cv2", "cyclopts", "librosa", "rich", "transformers"]
allowed = ["infrastructure"]
```

Hecate group matching is ordered. Put specific prefixes before general prefixes
so `beatcue.adapters.outbound` wins before `beatcue.adapters`.

Hecate supports `[[tool.hecate.ignore_imports]]` with `importer`, `imported`,
and non-empty `reason`. Use ignores only for documented composition-root
exceptions or other explicitly accepted edges. Do not use ignores to mask a
real boundary violation.

## Work plan

### Milestone 1: Reconfirm the baseline

Before editing implementation files, run and log the current gate behaviour:

```bash
make check-architecture 2>&1 | tee /tmp/check-architecture-baseline-beatcue-feat-plan-hecate-adoption.out
make check-fmt 2>&1 | tee /tmp/check-fmt-baseline-beatcue-feat-plan-hecate-adoption.out
make lint 2>&1 | tee /tmp/lint-baseline-beatcue-feat-plan-hecate-adoption.out
make test 2>&1 | tee /tmp/test-baseline-beatcue-feat-plan-hecate-adoption.out
```

If any baseline gate fails before the migration starts, stop. Record whether
the failure is unrelated pre-existing work or a blocker for this plan.

Use `leta grep ".*" "beatcue/architecture" -k function,method,class` and
`leta refs check_architecture` to confirm no production code depends on the
local checker API. Plain `rg` is acceptable for documentation, TOML, Makefile,
and test-string searches.

Run CodeRabbit after the baseline documentation and discovery milestone:

```bash
coderabbit review --agent
```

Clear all actionable concerns before moving to Milestone 2.

### Milestone 2: Add Hecate as the configured checker

Add Hecate to the development dependency group in `pyproject.toml` from the Git
commit:

```toml
"hecate @ git+https://github.com/leynos/hecate.git@46f8c8798e7a80a3a1ab5a13c2a000a4423ffc12",
```

Run dependency synchronization through the Makefile or `uv` only as required by
the existing workflow. Do not create an isolated Cargo or package cache.

Add `[tool.hecate]` to `pyproject.toml` using the policy from the Hecate
migration notes. Keep `include_external_packages = true` because BeatCue
classifies infrastructure libraries such as `cyclopts`, `rich`, `cv2`,
`librosa`, `transformers`, `cuprum`, and `cmdmox`.

Run:

```bash
$(UV_ENV) $(UV) run hecate check --format text 2>&1 | tee /tmp/hecate-direct-beatcue-feat-plan-hecate-adoption.out
$(UV_ENV) $(UV) run hecate check --format json 2>&1 | tee /tmp/hecate-json-beatcue-feat-plan-hecate-adoption.out
```

Expected result: the current `beatcue/` package exits `0` with no violations.
If Hecate reports unmatched package roots or configuration errors, fix the TOML
or package mapping before proceeding.

### Milestone 3: Prove policy parity with BeatCue fixtures

Adapt the existing fixture tests so they exercise Hecate rather than
`beatcue.architecture`. Keep tests that prove BeatCue's policy and remove tests
that only duplicate Hecate's internal parser, CLI, or re-export unit coverage.

The replacement tests should prove at least these behaviours:

- a domain fixture importing an outbound adapter fails;
- an application fixture importing an adapter directly fails;
- a re-exported adapter import remains visible and fails;
- a star-re-exported adapter import remains visible and fails;
- an inbound CLI fixture may import the composition root;
- the composition root fixture may wire outbound adapters;
- missing or invalid package roots return configuration failure semantics;
- `default_rule_id = "ARCH001"` appears in BeatCue diagnostics if that
  compatibility decision is retained.

Prefer using Hecate's CLI through `uv run hecate check --config <file>` for
behavioural parity tests. If creating fixture TOML files becomes noisy, use
temporary TOML files in pytest `tmp_path` fixtures and keep the policy content
small and explicit.

Run:

```bash
make test 2>&1 | tee /tmp/test-hecate-fixtures-beatcue-feat-plan-hecate-adoption.out
```

Expected result: tests pass and no BeatCue test imports
`beatcue.architecture.checker`, `beatcue.architecture.policy`, or
`beatcue.architecture.reexports` unless a deliberate compatibility wrapper has
been accepted in the Decision log.

Run CodeRabbit:

```bash
coderabbit review --agent
```

Clear all actionable concerns before moving to Milestone 4.

### Milestone 4: Replace Makefile wiring and remove local checker code

Change the Makefile `check-architecture` target to run:

```makefile
$(UV_ENV) $(UV) run hecate check
```

Keep the target name and keep `make lint` invoking it after Ruff and Pylint.

Remove the repository-local checker modules under `beatcue/architecture/` once
the tests no longer depend on them. If removing the whole package causes
packaging or import-discovery issues, remove the implementation modules first
and leave only a minimal deprecation wrapper for one commit. A wrapper is
acceptable only if the Decision log records why immediate removal would break a
documented interface.

Run:

```bash
make check-architecture 2>&1 | tee /tmp/check-architecture-hecate-beatcue-feat-plan-hecate-adoption.out
make lint 2>&1 | tee /tmp/lint-hecate-beatcue-feat-plan-hecate-adoption.out
```

Expected result: `make check-architecture` delegates to Hecate and `make lint`
still passes through the architecture gate.

### Milestone 5: Update documentation and decisions

Update `docs/adr-003-hexagonal-architecture-enforcement.md` if the existing ADR
can be amended cleanly. If the change is treated as a new decision, create the
next numbered ADR in `docs/` and reference it from
`docs/beatcue-technical-design.md`. The ADR must explain that BeatCue replaces
the local checker with pinned Hecate, why declarative TOML policy is preferred,
and how `make check-architecture` remains the stable workflow.

Update `docs/beatcue-technical-design.md` section 5 so it names Hecate as the
architecture fitness function rather than a future unspecified import-lint rule
or equivalent checker.

Update `docs/developers-guide.md` so "Architectural rules" and "Quality gates"
describe Hecate, `[tool.hecate]`, `hecate check`, the Makefile target, ordered
groups, re-export handling, and the rule for adding documented `ignore_imports`.

Update `docs/users-guide.md` only for externally visible changes. If no
end-user media-analysis CLI or library API changes, add at most a concise note
that source distributions run architecture validation through the documented
development gates, or leave the user guide unchanged and record that decision
in this plan.

Update `docs/roadmap.md` only after the implementation is complete and
validated. Mark the relevant entry as done if this migration creates a new
roadmap item, or add a decision note under the already completed task 1.2.2
that Hecate is now the implementation of the architecture fitness function.

Run Markdown-specific gates:

```bash
make fmt 2>&1 | tee /tmp/fmt-docs-hecate-beatcue-feat-plan-hecate-adoption.out
make markdownlint 2>&1 | tee /tmp/markdownlint-hecate-beatcue-feat-plan-hecate-adoption.out
make nixie 2>&1 | tee /tmp/nixie-hecate-beatcue-feat-plan-hecate-adoption.out
```

### Milestone 6: Final verification, review, and commit

Run the required final gates sequentially:

```bash
make check-fmt 2>&1 | tee /tmp/check-fmt-final-beatcue-feat-plan-hecate-adoption.out
make lint 2>&1 | tee /tmp/lint-final-beatcue-feat-plan-hecate-adoption.out
make test 2>&1 | tee /tmp/test-final-beatcue-feat-plan-hecate-adoption.out
```

Run CodeRabbit again:

```bash
coderabbit review --agent
```

Resolve all actionable CodeRabbit concerns. If a concern is intentionally not
fixed, record the rationale in this plan's Decision log and in the pull request
or review response.

Inspect the diff:

```bash
git status --short
git diff --stat
git diff
```

Commit with the `commit-message` skill workflow: write the message to a file
inside `mktemp -d`, then use `git commit -F`. Do not use `git commit -m`.

Suggested final commit subject:

```plaintext
Adopt Hecate for architecture checks
```

## Validation

For this planning-only change, validation means:

```bash
make check-fmt 2>&1 | tee /tmp/check-fmt-plan-beatcue-feat-plan-hecate-adoption.out
make lint 2>&1 | tee /tmp/lint-plan-beatcue-feat-plan-hecate-adoption.out
make test 2>&1 | tee /tmp/test-plan-beatcue-feat-plan-hecate-adoption.out
coderabbit review --agent
```

For the future implementation, validation means all commands in Milestone 6
pass, plus `make check-architecture` visibly runs Hecate.

## Progress

- [x] 2026-05-19: Loaded the `leta`, `hexagonal-architecture`,
  `execplans`, and `commit-message` skills.
- [x] 2026-05-19: Created a `leta` workspace for the BeatCue checkout.
- [x] 2026-05-19: Used a Wyvern agent team for read-only planning research.
- [x] 2026-05-19: Retrieved the pinned Hecate user, migration, and
  configuration documents from GitHub raw URLs.
- [x] 2026-05-19: Mapped the current local checker, Makefile gate, tests,
  fixtures, and documentation touchpoints.
- [x] 2026-05-19: Drafted this planning document.
- [x] 2026-05-19: Ran `make check-fmt`, `make lint`, and `make test` for the
  planning change.
- [x] 2026-05-19: Ran CodeRabbit on the planning change and fixed its
  line-wrap concern.
- [x] 2026-05-19: Reran validation after the first CodeRabbit fix.
- [x] 2026-05-19: Reran CodeRabbit and fixed the remaining prose concerns.
- [x] 2026-05-19: Reran validation after the prose fixes.
- [x] 2026-05-19: Reran CodeRabbit and removed an irrelevant skill mention.
- [x] 2026-05-19: Reran validation after the skill-list fix.
- [x] 2026-05-19: Reran CodeRabbit after the skill-list fix and fixed its
  remaining documentation-style concerns.
- [x] 2026-05-19: Reran validation after the documentation-style fixes.
- [x] 2026-05-19: Reran CodeRabbit after the documentation-style fixes and
  cleared all remaining concerns.
- [x] 2026-05-20: Committed the planning artefact.
- [x] 2026-05-20: Received explicit approval to implement the plan.
- [x] 2026-05-20: Reran the Milestone 1 baseline gates:
  `make check-architecture`, `make check-fmt`, `make lint`, and `make test` all
  passed. `make test` reported 34 passing tests.
- [x] 2026-05-20: Used `leta grep` and `leta refs check_architecture` to
  confirm that the local checker API is referenced by `beatcue.architecture`
  and architecture tests, not production BeatCue functionality.
- [x] 2026-05-20: Ran CodeRabbit for Milestone 1; it completed with zero
  findings.
- [x] 2026-05-20: Added Hecate as a pinned development dependency from
  `git+https://github.com/leynos/hecate.git@46f8c8798e7a80a3a1ab5a13c2a000a4423ffc12`.
- [x] 2026-05-20: Added the initial `[tool.hecate]` policy to `pyproject.toml`
  with ordered BeatCue groups, `include_external_packages = true`, and
  `default_rule_id = "ARCH001"`.
- [x] 2026-05-20: Ran direct Hecate checks. Text output reported
  `hecate: architecture check passed`; JSON output reported
  `{"ok": true, "violations": []}`.
- [x] 2026-05-20: Ran CodeRabbit for Milestone 2; it completed with zero
  findings.
- [x] 2026-05-20: Replaced local checker/parser/re-export tests with
  Hecate-backed BeatCue policy tests. The suite now covers forbidden fixture
  imports, allowed fixture graphs, current package acceptance, missing-root
  errors, and `ARCH001` diagnostics through `hecate.cli.main`.
- [x] 2026-05-20: Ran `make check-fmt`, `make lint`, and `make test` for
  Milestone 3. The test suite reported 11 passing tests.
- [x] 2026-05-20: Ran CodeRabbit for Milestone 3; it completed with zero
  findings.
- [x] 2026-05-20: Replaced the Makefile `check-architecture` implementation
  with `$(UV_ENV) $(UV) run hecate check` and removed the local
  `beatcue.architecture` checker package.
- [x] 2026-05-20: Ran `make check-architecture`, `make lint`, and `make test`
  after removing the local checker. The architecture gate now prints
  `hecate: architecture check passed`, lint includes that gate, and the test
  suite still reports 11 passing tests.
- [x] 2026-05-20: Ran CodeRabbit for Milestone 4; it completed with zero
  findings.
- [x] 2026-05-20: Updated documentation for the Hecate migration. ADR 003 is
  superseded by ADR 005, the technical design and developers' guide name Hecate
  as the active fitness function, the users' guide documents the
  contributor-facing architecture check, and roadmap task 1.2.2 notes Hecate as
  the implementation.
- [x] 2026-05-20: Ran documentation gates for Milestone 5. `make
  markdownlint` and `make nixie` both passed after unrelated formatter churn
  from a failed repository-wide `make fmt` run was reversed.
- [x] 2026-05-20: Ran CodeRabbit for Milestone 5 after several recoverable
  service rate-limit responses; the completed review reported zero findings.
- [x] 2026-05-20: Implemented the Hecate replacement after approval.
- [x] 2026-05-20: Ran final validation. `make check-fmt`, `make lint`, `make
  test`, `make markdownlint`, and `make nixie` all passed. `make lint` ran the
  Hecate-backed `make check-architecture` gate and reported
  `hecate: architecture check passed`.
- [x] 2026-05-20: Ran final CodeRabbit review after one recoverable rate-limit
  response; the completed review reported zero findings.
- [x] 2026-05-20: Marked the relevant roadmap entry done after implementation
  validation. Roadmap task 1.2.2 is checked and names Hecate as the
  implementation.

## Surprises & discoveries

- The raw Hecate documents exist at the requested commit under the
  `leynos/hecate` repository and describe the expected architecture-checking
  tool.
- Looking for the Hecate commit inside the BeatCue repository fails because the
  SHA belongs to a different repository. This is expected, but easy to confuse
  during local-only investigation.
- The public package name `hecate` may collide with unrelated historical
  packages. The implementation must use the pinned Git URL.
- Hecate's BeatCue migration notes already provide a TOML translation of the
  current local policy, including `include_external_packages = true` and
  `default_rule_id = "ARCH001"`.
- Repository-wide `make fmt` currently reports pre-existing Markdown lint
  issues in older documents outside this plan. The planning change was
  validated with the requested code gates and targeted Markdown lint for this
  file.
- Repository-wide `make fmt` still reports pre-existing Markdown line-length
  findings outside the Hecate migration. Its partial formatter changes were
  limited to unrelated documentation and reversed before the Milestone 5
  documentation gates were rerun.
- Baseline validation on 2026-05-20 was clean before implementation edits:
  `make check-architecture`, `make check-fmt`, `make lint`, and `make test`
  passed on the repository-local checker.
- `leta refs check_architecture` found references only in the local
  architecture package and tests, which means removing `beatcue.architecture`
  does not currently affect production BeatCue code.
- Hecate installed successfully from the requested Git commit through `uv`.
  The installed version reports as `hecate==0.1.0`, but the source is pinned to
  commit `46f8c8798e7a80a3a1ab5a13c2a000a4423ffc12`.
- Hecate reports missing package-root configuration errors to stderr with exit
  code `2`.
- For the star re-export fixture, Hecate reports the forbidden adapter barrel
  and public symbol as an `application -> adapter` violation. This still
  catches the hidden adapter dependency, but the text diagnostic does not name
  the outbound origin for that specific star-export path.
- Ruff's security rules reject `subprocess` use in the Hecate tests. Calling
  `hecate.cli.main` directly keeps the tests inside the current interpreter and
  still exercises the supported CLI argument surface.
- Removing `beatcue.architecture` did not require a compatibility wrapper. The
  symbol-reference check and migrated tests confirmed it was an internal
  fitness-function implementation rather than a public BeatCue API.
- The Hecate replacement is substantive enough to need a new ADR rather than
  an in-place edit to ADR 003. ADR 003 now remains as historical context and
  ADR 005 records the active decision.

## Decision log

- 2026-05-19: Treat the raw GitHub documents at Hecate commit
  `46f8c8798e7a80a3a1ab5a13c2a000a4423ffc12` as the authoritative migration
  source. Rationale: the user provided those URLs and direct retrieval from
  `raw.githubusercontent.com/leynos/hecate` succeeds.
- 2026-05-19: Keep `make check-architecture` as the stable contributor command
  and change only its implementation during the future migration. Rationale:
  this preserves the documented workflow and limits user-visible churn.
- 2026-05-19: Plan to configure `default_rule_id = "ARCH001"`. Rationale:
  BeatCue's existing docs and tests use `ARCH001`, and Hecate supports
  configurable default rule identifiers.
- 2026-05-19: Do not mark the roadmap entry done during plan drafting.
  Rationale: the requested replacement must be approved before implementation,
  so the feature is incomplete.
- 2026-05-20: Begin implementation after explicit approval. Rationale: the
  approval gate is now satisfied, but roadmap completion remains blocked until
  Hecate is installed, wired, documented, validated, and reviewed.
- 2026-05-20: Keep `ARCH001` as BeatCue's Hecate rule identifier. Rationale:
  direct Hecate checks accept `default_rule_id = "ARCH001"`, which preserves
  the current diagnostic identifier while migrating the enforcement engine.
- 2026-05-20: Accept Hecate's star re-export diagnostic shape for BeatCue
  fixture tests. Rationale: the violation still fails the architecture gate and
  identifies the forbidden adapter barrel; preserving the old local checker's
  exact outbound-origin wording is less important than enforcing the boundary
  through the shared tool.
- 2026-05-20: Remove `beatcue.architecture` instead of keeping a deprecation
  wrapper. Rationale: no production code depends on it, the Makefile target is
  the documented contributor interface, and keeping a wrapper would preserve a
  second checker surface after Hecate becomes the enforcement engine.
- 2026-05-20: Create ADR 005 and supersede ADR 003. Rationale: replacing the
  enforcement engine and moving policy into TOML is a substantive architecture
  decision, while ADR 003 is still useful history for why the gate exists.

## Outcomes & retrospective

BeatCue now uses Hecate, pinned from
`git+https://github.com/leynos/hecate.git@46f8c8798e7a80a3a1ab5a13c2a000a4423ffc12`,
as the single architecture checker behind `make check-architecture`.
`beatcue.architecture` was removed, and BeatCue's policy now lives under
`[tool.hecate]` in `pyproject.toml` with `default_rule_id = "ARCH001"`.

The replacement preserves the contributor-facing Makefile workflow:
`make lint` still runs Ruff, Pylint, and the architecture gate, and the
architecture gate now reports `hecate: architecture check passed` for the
current package. Hecate-backed fixture tests cover forbidden imports, allowed
graphs, re-export visibility, current-package acceptance, and configuration
errors.

Final validation on 2026-05-20 passed:

- `make check-fmt`
- `make lint`
- `make test`
- `make markdownlint`
- `make nixie`

CodeRabbit reviews completed with zero findings for every implementation
milestone after any recoverable rate-limit waits. Documentation now records
Hecate as the active architecture fitness function in ADR 005, the technical
design, the developers' guide, the users' guide, and the roadmap.

Follow-up: repository-wide `make fmt` still reports pre-existing Markdown
line-length findings outside the Hecate migration. This migration did not take
ownership of that older documentation debt.
