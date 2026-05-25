# Create the package skeleton for BeatCue's architecture

This ExecPlan (execution plan) is a living document. The sections
`Constraints`, `Tolerances`, `Risks`, `Progress`, `Surprises & discoveries`,
`Decision log`, and `Outcomes & retrospective` must be kept up to date as work
proceeds.

Status: COMPLETE

Implementation began after explicit approval in the user request dated
2026-05-20 and completed on 2026-05-25.

## Purpose / big picture

BeatCue's technical design depends on a stable hexagonal package boundary:
domain code at the centre, application services around it, adapters at the
edge, and `beatcue.config` as the composition root that wires concrete
implementations. Roadmap item 1.2.2 has already added a local architecture
checker, but the production package still lacks the real
`beatcue.domain`, `beatcue.application`, `beatcue.adapters`, and
`beatcue.config` packages that later work will inhabit.

After this plan is approved and implemented, a contributor can inspect the
package tree and see the intended boundary before any infrastructure adapters
land. Running `make check-architecture` or `make lint` will scan the real
production packages and continue to reject imports that point outward from the
domain or application layers. The observable result is a small importable
skeleton, not domain models, use cases, command-line behaviour, or media I/O.

## Constraints

- Read and follow `AGENTS.md` before changing the repository.
- Use the `leta` skill for code navigation and keep the Leta workspace current.
- Use the `hexagonal-architecture` skill as the architectural rule source:
  dependencies point inward, the domain owns ports, and adapters implement or
  drive those ports.
- Use the `execplans` skill and keep this file self-contained and current.
- Do not implement BeatCue domain value objects, port protocols, application
  services, CLI commands, writer adapters, media adapters, configuration
  binding, or dependency groups in this task.
- Include placeholder modules only where they express a real boundary. For this
  task, package `__init__.py` files are acceptable boundary markers; empty
  `ports.py`, `analyse.py`, `compose.py`, or adapter implementation modules are
  not acceptable unless the approved implementation adds real behaviour.
- Preserve the existing public smoke API: `from beatcue import hello` must
  still work and return `"hello from Python"`.
- Preserve the existing architecture checker and do not weaken forbidden-import
  rules to make the new packages pass.
- Keep `beatcue.config` as the only production package allowed to import both
  application services and concrete outbound adapters.
- Do not mark roadmap item 1.2.1 done until the approved implementation,
  documentation updates, quality gates, CodeRabbit review, and commit are
  complete.
- Prefer Makefile targets over direct tool commands for gates.
- Run formatting, linting, typechecking, architecture checks, and tests
  sequentially. Do not run those gates in parallel.
- Use `tee` for long gate output with log files under `/tmp`, following the
  project naming convention:

```bash
/tmp/$ACTION-$(basename "$(pwd)")-$(git branch --show-current).out
```

- Use `coderabbit review --agent` after each major implementation milestone,
  clear all concerns before moving to the next milestone, and record the result
  in this plan.
- Commit only after the relevant gates pass.

If satisfying the objective requires violating any constraint, stop, document
the conflict in `Decision log`, and ask for direction.

## Tolerances (exception triggers)

- Scope: stop and escalate if implementation needs more than ten production
  files or more than 250 net production lines outside tests and documentation.
- Dependencies: stop and escalate before adding any runtime dependency.
- Development dependencies: pytest-bdd is requested for behavioural validation
  but roadmap item 1.2.3 owns general development-dependency wiring. If
  pytest-bdd is not already available and adding it would require touching
  dependency lock files or widening 1.2.3, stop and ask whether to include that
  overlap in 1.2.1.
- Interface: stop and escalate before changing the public `beatcue` import
  surface beyond adding importable boundary packages.
- Architecture policy: stop and escalate if the existing checker cannot model
  the production packages without weakening the domain or application rules.
- CLI package shape: stop and present options if implementing the skeleton
  requires deciding between a top-level `beatcue.cli` package and
  `beatcue.adapters.inbound.cli` as the future command-line home. The default
  path for 1.2.1 is to avoid creating either CLI module because neither carries
  real behaviour yet.
- Tests: stop and escalate if the full required gate set still fails after two
  focused fix attempts.
- Documentation: stop and escalate if completing 1.2.1 requires a new
  architectural decision record (ADR) rather than updating existing design and
  guide text.

## Risks

- Risk: creating empty modules could look like progress while adding no
  enforceable boundary.
  Severity: medium.
  Likelihood: medium.
  Mitigation: limit production additions to package boundary files and add
  tests that prove those packages are importable and classified by the
  architecture policy.

- Risk: roadmap item 1.2.2 is already complete while 1.2.1 is still open, so
  tests may already cover future-shape fixtures rather than the real package.
  Severity: low.
  Likelihood: high.
  Mitigation: add production-package checks that assert the newly created
  packages participate in the same policy as the fixtures.

- Risk: the current design references both `beatcue.cli` and
  `beatcue.adapters.inbound.cli`.
  Severity: medium.
  Likelihood: medium.
  Mitigation: do not create a command-line module in this task unless a real
  boundary requires it. If documentation must be clarified, make the smallest
  guide update and record the decision here.

- Risk: the user's requested pytest-bdd behavioural validation may overlap with
  roadmap item 1.2.3, which is scheduled to wire pytest-bdd and other
  development dependencies after 1.2.1.
  Severity: medium.
  Likelihood: medium.
  Mitigation: first check whether pytest-bdd is already available in the
  environment. If not, use the tolerance above to ask whether to add the dev
  dependency in this task or defer behavioural coverage until 1.2.3.

- Risk: Markdown or full Python gates may fail because of unrelated repository
  state.
  Severity: medium.
  Likelihood: low.
  Mitigation: capture tee logs, distinguish pre-existing failures from new
  failures, and do not commit until the required gates for this change pass or
  the user gives explicit direction.

## Relevant documentation and skills

This plan depends on the following local documents:

- `docs/roadmap.md` §1.2, especially roadmap item 1.2.1.
- `docs/beatcue-technical-design.md` §§5-8 for the hexagonal boundary,
  package structure, domain model, and port ownership.
- `docs/beatcue-technical-design.md` §17 for testing and verification
  expectations.
- `docs/developers-guide.md` for contributor-facing architecture rules.
- `docs/users-guide.md` for current public behaviour. This task should update
  it only if the package skeleton changes a user-visible import contract.
- `docs/adr-002-v1-port-surface.md` for the required versus post-v1 port
  distinction.
- `docs/adr-003-hexagonal-architecture-enforcement.md` for the local checker
  and its fixture strategy.
- `docs/complexity-antipatterns-and-refactoring-strategies.md` for keeping
  any new tests or checker changes small and readable.
- `.rules/python-*.md` if Python implementation details become necessary.

The required skills are:

- `leta`, for semantic code navigation and workspace setup.
- `hexagonal-architecture`, for inward dependency rules and port ownership.
- `execplans`, for this plan and its approval gate.
- `firecrawl-mcp`, for prior-art checks requested by the user.

Firecrawl prior-art research found that Import Linter documents explicit
architecture contracts, including forbidden imports and layered rules, for
Python packages.[^1] BeatCue already has a local checker that serves the same
fitness-function role, so this implementation should extend and exercise the
existing checker rather than introduce Import Linter during 1.2.1.

## Current repository orientation

The repository root contains the package directly under `beatcue/`, not under a
`src/` directory. The current package includes `beatcue.__init__`,
`beatcue._hello`, `beatcue.pure`, and the local architecture checker under
`beatcue.architecture`.

The architecture checker is invoked by:

```bash
python -m beatcue.architecture
make check-architecture
make lint
```

The current policy classifies the future packages as these groups:

- `beatcue.domain` represents the `domain` group and may import only domain
  modules.
- `beatcue.application` belongs to the `application` group and may import
  application and domain modules.
- Inbound adapter code lives under `beatcue.adapters.inbound`; the policy also
  treats a future `beatcue.cli` module as inbound.
- Outbound adapter implementations live under `beatcue.adapters.outbound`.
- The broader `beatcue.adapters` package contains shared adapter-side code.
- `beatcue.config` acts as the composition root.

The existing tests already prove the policy with fixtures under
`tests/fixtures/architecture/`. This task should add coverage for the
production package skeleton, so the real package tree becomes part of the
fitness check.

## Implementation plan

### Milestone 1: Confirm the baseline

Confirm the current branch is not the main branch:

```bash
git branch --show-current
```

Confirm the worktree state before editing:

```bash
git status --short
```

Use Leta to inspect the architecture checker symbols rather than browsing
source files manually:

```bash
leta grep ".*" "beatcue/architecture" -k class,function --head 200
leta show _beatcue_groups -n 20
leta show check_architecture -n 12
```

Run the current architecture checker before changes and capture the result:

```bash
make check-architecture 2>&1 | tee \
  "/tmp/check-architecture-$(basename "$(pwd)")-$(git branch --show-current).out"
```

If this baseline fails, stop and record the failure before editing production
packages.

### Milestone 2: Add red tests for the real skeleton

Add unit tests before production files. The tests should fail because the
boundary packages do not exist yet. The likely test home is
`tests/test_architecture_checker.py` unless a more focused file is clearer.

The tests should cover these behaviours:

- `beatcue.domain`, `beatcue.application`, `beatcue.adapters`, and
  `beatcue.config` are importable production packages.
- `beatcue.adapters.inbound` and `beatcue.adapters.outbound` are importable
  adapter subpackages because the policy distinguishes them.
- The default production policy classifies each new package into the expected
  architecture group.
- `check_architecture()` accepts the production package after the skeleton
  exists.
- Existing fixture tests still reject outward imports and re-export bypasses.

If pytest-bdd is available or approved for addition, add one behavioural
scenario that expresses the user-facing development workflow:

```gherkin
Feature: Architecture package skeleton

  Scenario: The production package exposes the hexagonal boundary
    Given the BeatCue package skeleton is installed
    When the architecture checker runs against the production package
    Then the domain, application, adapter, and config packages are classified
    And the architecture checker reports no production boundary violations
```

This task does not introduce output formats, so syrupy snapshots are not
relevant. It does not introduce business invariants over a broad input space
except policy classification; if the existing Hypothesis policy tests do not
cover the new production package prefixes, add a small property test for that
classification. It does not introduce contractual business logic that would
justify CrossHair, a Rust extension, or Verus.

Run the focused red test command and record the expected failure:

```bash
uv run pytest -q tests/test_architecture_checker.py 2>&1 | tee \
  "/tmp/test-architecture-red-$(basename "$(pwd)")-$(git branch --show-current).out"
```

If the tests pass before the skeleton exists, tighten the tests so they prove
the intended package presence rather than only the existing fixture policy.

### Milestone 3: Create the smallest production package skeleton

Create these production package boundary files:

```plaintext
beatcue/domain/__init__.py
beatcue/application/__init__.py
beatcue/adapters/__init__.py
beatcue/adapters/inbound/__init__.py
beatcue/adapters/outbound/__init__.py
beatcue/config/__init__.py
```

Each file should contain a short package docstring and, if useful, an empty
`__all__` tuple. The files should not import across layers. Do not add
`ports.py`, `analyse.py`, `compose.py`, `cli.py`, or adapter implementation
modules in this milestone because those names imply behaviour owned by later
roadmap items.

The package docstrings should be contributor-facing rather than public API
marketing. They should explain the boundary in one sentence, for example:

```python
"""Pure BeatCue domain values, services, and port protocols."""
```

After creating the skeleton, run the focused tests again and expect them to
pass:

```bash
uv run pytest -q tests/test_architecture_checker.py 2>&1 | tee \
  "/tmp/test-architecture-green-$(basename "$(pwd)")-$(git branch --show-current).out"
```

Run CodeRabbit for the skeleton milestone:

```bash
coderabbit review --agent
```

Clear every concern before continuing. If CodeRabbit raises a scope concern
that conflicts with this plan, record the options in `Decision log` and ask for
direction.

### Milestone 4: Align documentation

Update documentation only where the skeleton changes the repository contract.
Expected edits are:

- `docs/developers-guide.md`: replace wording that says planned packages do not
  exist with wording that says the boundary packages now exist, but most
  behavioural modules remain future work.
- `docs/roadmap.md`: after implementation and validation are complete, mark
  item 1.2.1 as done and add a concise decision or success note.
- This ExecPlan: update `Progress`, `Surprises & discoveries`,
  `Decision log`, and later `Outcomes & retrospective`.

Do not update `docs/users-guide.md` unless the approved implementation exposes
a new user-visible import that a library consumer should know about. A package
skeleton with no domain values or use cases probably remains developer-facing.

Do not add a new ADR unless implementation forces a substantive architecture
decision, such as resolving the `beatcue.cli` versus
`beatcue.adapters.inbound.cli` discrepancy. If that happens, stop under the
documentation tolerance and ask for approval before widening the task.

### Milestone 5: Run full validation

Run the required gates sequentially. Use tee logs under `/tmp`.

```bash
make check-fmt 2>&1 | tee \
  "/tmp/check-fmt-$(basename "$(pwd)")-$(git branch --show-current).out"
make typecheck 2>&1 | tee \
  "/tmp/typecheck-$(basename "$(pwd)")-$(git branch --show-current).out"
make lint 2>&1 | tee \
  "/tmp/lint-$(basename "$(pwd)")-$(git branch --show-current).out"
make test 2>&1 | tee \
  "/tmp/test-$(basename "$(pwd)")-$(git branch --show-current).out"
make markdownlint 2>&1 | tee \
  "/tmp/markdownlint-$(basename "$(pwd)")-$(git branch --show-current).out"
make nixie 2>&1 | tee \
  "/tmp/nixie-$(basename "$(pwd)")-$(git branch --show-current).out"
```

The user specifically requested `make check-fmt`, `make typecheck`,
`make lint`, and `make test`; Markdown gates are required because this plan and
likely roadmap/developer-guide updates are Markdown changes.

Run CodeRabbit again after the validation milestone:

```bash
coderabbit review --agent
```

Clear all concerns before committing.

### Milestone 6: Commit

Review the final diff:

```bash
git diff --check
git diff --stat
git diff
```

Commit the approved, validated change with the `commit-message` skill. The
commit should be focused on roadmap item 1.2.1. A suitable subject is:

```plaintext
Create architecture package skeleton
```

After committing, update this plan's `Outcomes & retrospective` with the commit
hash, validation logs, CodeRabbit result, and any follow-up work left for
1.2.3 or later roadmap items.

## Acceptance criteria

- `beatcue.domain`, `beatcue.application`, `beatcue.adapters`,
  `beatcue.adapters.inbound`, `beatcue.adapters.outbound`, and
  `beatcue.config` exist as importable packages.
- The new production files contain only boundary-bearing package metadata and
  do not import outward across the hexagonal boundary.
- The existing public smoke API still works.
- Unit tests prove the production package skeleton is importable and classified
  by the architecture policy.
- Behavioural pytest-bdd coverage is added if the dependency is already
  available or if the user approves adding it during this task.
- No syrupy snapshot is added unless the implementation introduces an output
  format or stable external payload, which is not expected.
- No CrossHair, Rust extension, or Verus proof is added because this task does
  not introduce business logic that benefits from formal proof.
- `make check-architecture`, `make check-fmt`, `make typecheck`, `make lint`,
  `make test`, `make markdownlint`, and `make nixie` pass.
- CodeRabbit reports no unresolved concerns after each major milestone.
- `docs/roadmap.md` marks roadmap item 1.2.1 done only after the approved
  implementation has passed gates.

## Progress

- [x] (2026-05-19T13:18:31+02:00) Loaded the `leta`,
  `hexagonal-architecture`, `execplans`, and `firecrawl-mcp` skills.
- [x] (2026-05-19T13:18:31+02:00) Created the Leta workspace for this
  worktree.
- [x] (2026-05-19T13:18:31+02:00) Confirmed the current branch is
  `feat/leta-hex-plan-setup`, not a main branch.
- [x] (2026-05-19T13:18:31+02:00) Used a Wyvern agent, Copernicus, to inspect
  roadmap, design, guide, checker, and package constraints for this planning
  task.
- [x] (2026-05-19T13:18:31+02:00) Used Firecrawl to check prior art for
  Python architecture import-boundary tooling.
- [x] (2026-05-19T13:18:31+02:00) Drafted this ExecPlan.
- [x] (2026-05-19T13:18:31+02:00) Validated the draft with
  `make markdownlint`, `make nixie`, `make check-fmt`, `make typecheck`,
  `make lint`, and `make test`.
- [x] (2026-05-19T13:18:31+02:00) Ran `coderabbit review --agent`; it
  reported zero findings after minor prose fixes.
- [x] (2026-05-20T23:53:43+02:00) Received explicit approval to implement this
  ExecPlan.
- [x] (2026-05-20T23:53:43+02:00) Confirmed the baseline architecture gate
  with `make check-architecture`; it passed.
- [x] (2026-05-20T23:53:43+02:00) Checked `pytest-bdd` availability with
  `uv run python`; it is not installed in the current dev environment.
- [x] (2026-05-25T23:28:20+02:00) Received user approval to install
  `pytest-bdd`, then added it to the dev dependency group with
  `uv add --group dev pytest-bdd`.
- [x] (2026-05-25T23:28:20+02:00) Added red unit tests and a pytest-bdd
  scenario for the production package skeleton. The focused red run failed
  because `beatcue.domain`, `beatcue.application`, `beatcue.adapters`, and
  `beatcue.config` do not exist yet.
- [x] (2026-05-25T23:28:20+02:00) Created boundary-only
  `__init__.py` files for `beatcue.domain`, `beatcue.application`,
  `beatcue.adapters`, `beatcue.adapters.inbound`, `beatcue.adapters.outbound`,
  and `beatcue.config`.
- [x] (2026-05-25T23:28:20+02:00) Reran the focused architecture tests;
  `tests/test_architecture_checker.py` and
  `tests/test_architecture_package_skeleton_bdd.py` passed.
- [x] (2026-05-25T23:43:00+02:00) Ran `make check-fmt`, `make typecheck`,
  `make lint`, `make test`, `make markdownlint`, and `make nixie`, then ran
  `coderabbit review --agent` for the skeleton milestone. CodeRabbit reported
  two trivial test-cleanup findings; both were valid, fixed, and revalidated
  with the full deterministic gate set. The follow-up CodeRabbit review
  reported zero findings.
- [x] (2026-05-25T23:50:00+02:00) Aligned `docs/developers-guide.md` with the
  new production boundary packages and checked off roadmap item 1.2.1 in
  `docs/roadmap.md`.
- [x] (2026-05-25T23:58:00+02:00) Reran the full required gate set after the
  documentation and roadmap updates: `make check-fmt`, `make typecheck`,
  `make lint`, `make test`, `make markdownlint`, and `make nixie` all passed.
- [x] (2026-05-25T23:58:00+02:00) Ran `coderabbit review --agent` for the
  validation milestone; it reported zero findings.
- [x] (2026-05-25T23:58:00+02:00) Committed the package skeleton milestone as
  `da95b51`.
- [x] (2026-05-25T23:50:00+02:00) Marked roadmap item 1.2.1 done.

## Surprises & discoveries

- Observation: roadmap item 1.2.2 is already complete, even though 1.2.1 is
  still open.
  Evidence: `docs/roadmap.md` marks 1.2.2 done and 1.2.1 not done.
  Impact: implementation should not build a new checker. It should make the
  existing checker meaningful against the production packages created by
  1.2.1.

- Observation: the architecture policy already includes package prefixes for
  `beatcue.domain`, `beatcue.application`, `beatcue.adapters`,
  `beatcue.adapters.inbound`, `beatcue.adapters.outbound`, `beatcue.config`,
  and a future `beatcue.cli`.
  Evidence: `beatcue/architecture/policy.py` defines those groups in
  `_beatcue_groups`.
  Impact: the skeleton probably needs no policy change unless tests expose a
  classification gap.

- Observation: the technical design mentions `beatcue.cli` as an inbound
  adapter, while the package-structure section places CLI under
  `beatcue.adapters.inbound.cli`.
  Evidence: `docs/beatcue-technical-design.md` §§5-6.
  Impact: this task should not settle the CLI module location by creating a
  placeholder CLI. If a decision becomes unavoidable, escalate or document it
  separately.

- Observation: Import Linter prior art supports the same general
  fitness-function approach already present in BeatCue.
  Evidence: Firecrawl retrieved Import Linter documentation describing
  forbidden contracts and layered architecture contracts for Python packages.
  Impact: keep 1.2.1 focused on BeatCue's local checker and avoid adding a
  redundant dependency.

- Observation: `pytest-bdd` is not available in the current development
  environment.
  Evidence: `uv run python` reported `ModuleNotFoundError` for `pytest_bdd`.
  Impact: behavioural coverage for this task requires either adding the
  development dependency earlier than roadmap item 1.2.3 or deferring
  pytest-bdd coverage until 1.2.3 wires the requested test dependencies.

## Decision log

- Decision: The default implementation path creates only package
  `__init__.py` files for `domain`, `application`, `adapters`,
  `adapters.inbound`, `adapters.outbound`, and `config`.
  Rationale: those files express the real package boundary without implying
  domain models, ports, application services, CLI commands, or adapters that
  later roadmap tasks own.
  Date: 2026-05-19.

- Decision: The default implementation path does not create `beatcue.cli` or
  `beatcue.adapters.inbound.cli`.
  Rationale: the design has a documented location ambiguity, and no actual CLI
  behaviour exists in 1.2.1. Creating a placeholder would make the ambiguity
  look settled without delivering behaviour.
  Date: 2026-05-19.

- Decision: This plan treats syrupy snapshots, CrossHair, Rust extensions, and
  Verus proofs as not applicable unless implementation scope changes.
  Rationale: 1.2.1 introduces package boundaries and architecture-fitness
  checks, not output formats, business invariants, or formal domain logic.
  Date: 2026-05-19.

- Decision: Add `pytest-bdd` in roadmap item 1.2.1 after explicit user
  approval.
  Rationale: behavioural coverage is requested for this task, and waiting for
  1.2.3 would leave the package-skeleton workflow without the planned
  behavioural scenario.
  Date: 2026-05-25.

## Outcomes & retrospective

Roadmap item 1.2.1 is complete. The production package now exposes
boundary-only packages for `beatcue.domain`, `beatcue.application`,
`beatcue.adapters`, `beatcue.adapters.inbound`, `beatcue.adapters.outbound`,
and `beatcue.config`. Each package is importable and intentionally contains no
cross-layer imports or behaviour modules.

The architecture coverage now checks the real package skeleton in unit tests
and in a pytest-bdd scenario. `pytest-bdd` was added to the development
dependency group after explicit user approval so the behavioural test could
land with this task.

`docs/developers-guide.md` now describes the production boundary packages as
present, `docs/roadmap.md` marks 1.2.1 done, and no user-facing API or CLI
behaviour changed. `docs/users-guide.md` therefore did not need an update.

Validation passed with `make check-fmt`, `make typecheck`, `make lint`,
`make test`, `make markdownlint`, and `make nixie`. CodeRabbit reported two
valid trivial test-cleanup findings during the skeleton milestone; both were
fixed, revalidated, and followed by a zero-finding review. The final validation
milestone CodeRabbit review also reported zero findings.

No follow-up work remains for 1.2.1. Later roadmap items still own concrete
domain values, application services, CLI wiring, adapter implementations, and
the remaining design dependencies.

[^1]: Import Linter documentation, "Import Linter", accessed 2026-05-19,
    <https://import-linter.readthedocs.io/en/v2.4/readme.html>.
