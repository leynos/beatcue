# Import hexagonal architecture enforcement

This ExecPlan (execution plan) is a living document. The sections `Constraints`,
`Tolerances`, `Risks`, `Progress`, `Surprises & Discoveries`, `Decision Log`,
and `Outcomes & Retrospective` must be kept up to date as work proceeds.

Status: COMPLETE

## Purpose / big picture

BeatCue already documents a strict hexagonal architecture: domain code sits at
the centre, application services orchestrate use cases, adapters handle
infrastructure, and `beatcue.config` is the narrow composition root that wires
concrete dependencies. The current repository is still a skeleton, so ordinary
tests cannot yet catch future import-boundary drift.

This work imports and trials Episodic's repository-local architecture checker
in BeatCue. A contributor will be able to run `make check-architecture` or
`make lint` and see the build fail if domain or application code imports
adapters, if adapter barrel modules hide forbidden imports through package
re-exports, or if the composition-root exception cannot be represented
narrowly. The trial also records a postmortem that decides what should be
extracted before trying the same mechanism in Prosidy Darn.

The observable end state is:

- `python -m beatcue.architecture` reports violations with stable diagnostics;
- `make check-architecture` checks the current `beatcue` package;
- `make lint` includes the architecture gate after Ruff;
- architecture tests prove forbidden and allowed future-shape package graphs;
- BeatCue documentation explains the enforced boundary and its scope;
- the ExecPlan's `Outcomes & Retrospective` answers the required reuse
  questions with citations to prior art.

## Constraints

- Read and follow `AGENTS.md` before changing the repository.
- Do not begin implementation until this draft ExecPlan is explicitly approved.
- Do not copy Episodic's module groups directly into BeatCue.
- Do not weaken BeatCue's documented boundary to make the checker pass.
- Preserve the public smoke API: `from beatcue import hello` must continue to
  return `"hello from Python"`.
- Do not implement unrelated BeatCue domain, application, or adapter modules
  just to satisfy the checker. Use test fixture packages for future-shape
  policy proof.
- Do not add a runtime dependency.
- Do not add a heavyweight dev dependency without documenting the trade-off and
  obtaining approval if a tolerance requires escalation.
- Use Python's standard-library `ast` unless the implementation proves it is
  inadequate within the tolerances below.
- Keep the checker local to BeatCue for this trial. Shared-tool extraction is a
  retrospective recommendation, not part of this implementation.
- Prefer Makefile targets over direct tool commands.
- Run long test, lint, typecheck, format, Markdown, and architecture commands
  with `tee` to a `/tmp` log file named for the action and branch.
- Do not run format, lint, typecheck, tests, or architecture gates in parallel.
- Commit only after the required gates pass.
- Rename the branch to `import-hex-architecture-enforcement`, set it to track
  `origin/import-hex-architecture-enforcement`, push it, and open a draft PR.
- Mention this ExecPlan document in the draft PR summary.

If satisfying the objective requires violating any constraint, stop, document
the conflict in `Decision Log`, and ask for direction.

## Tolerances (exception triggers)

- Scope: stop and escalate if the implementation requires more than 12
  production files or more than 700 net new production lines.
- Dependencies: stop and escalate before adding any runtime dependency.
- Dependencies: stop and escalate before adding more than one dev dependency.
- Policy shape: stop and escalate if the checker cannot represent
  `beatcue.config` as a narrow composition-root exception.
- Re-export handling: stop and escalate if re-export handling becomes
  substantially more complex than Episodic's current mechanism.
- Interface: stop and escalate before changing public API behaviour, including
  `beatcue.hello`.
- Quality iterations: stop and escalate if all gates still fail after three
  focused fix attempts.
- Ambiguity: stop and present options if two valid policy interpretations would
  materially change what BeatCue allows.

## Risks

- Risk: BeatCue's current flat skeleton has too few real modules to prove the
  future package layout. Severity: medium. Likelihood: high. Mitigation: keep
  production checks pointed at the current package while using small fixture
  packages under `tests/fixtures/architecture/` for future-shape rules.

- Risk: a hard-coded Python policy may become awkward as BeatCue's package
  graph grows. Severity: medium. Likelihood: medium. Mitigation: implement the
  smallest policy surface now, then answer whether TOML or JSON configuration
  is needed in the postmortem.

- Risk: package barrel re-exports could hide adapter imports if resolution is
  incomplete. Severity: high. Likelihood: medium. Mitigation: adapt Episodic's
  re-export scanner and add tests for explicit, star, nested star, and
  `__all__`-controlled re-exports as needed.

- Risk: documentation gates may fail because the new ExecPlan and ADR must
  obey the repository Markdown style. Severity: low. Likelihood: medium.
  Mitigation: wrap Markdown at 80 columns, use labelled code fences, run
  `make markdownlint`, and run `make nixie` if Markdown changes include or
  touch Mermaid diagrams.

- Risk: `make test` or `make typecheck` may require environment writes or
  dependency downloads in a read-only or network-restricted sandbox. Severity:
  medium. Likelihood: medium. Mitigation: use approved Makefile targets first;
  if a command fails for sandbox or network reasons, rerun it with elevated
  permissions and record the result.

## Progress

- [x] (2026-05-10T20:31:41Z) Read root `AGENTS.md`; no nested `AGENTS.md`
  files exist.
- [x] (2026-05-10T20:31:41Z) Loaded the `execplans`, `leta`, and
  `firecrawl-mcp` skills required by the task and repository instructions.
- [x] (2026-05-10T20:31:41Z) Confirmed the current branch is
  `feat/import-hex-enforcement`, not the main branch.
- [x] (2026-05-10T20:31:41Z) Inspected BeatCue's current skeleton,
  Makefile, `pyproject.toml`, technical design, developers' guide,
  architectural decision records (ADRs), and smoke test.
- [x] (2026-05-10T20:31:41Z) Located and reviewed the referenced Episodic
  checker, policy, re-export resolver, tests, behaviour-driven development
  (BDD) feature, BDD steps, and ADR.
- [x] (2026-05-10T20:31:41Z) Performed a prior-art check for Import Linter,
  Semgrep, and Astroid using Firecrawl.
- [x] (2026-05-10T20:31:41Z) Drafted this ExecPlan.
- [x] (2026-05-10T21:08:54Z) Renamed the branch to
  `import-hex-architecture-enforcement`, pushed it, set upstream tracking to
  `origin/import-hex-architecture-enforcement`, and opened draft PR #8 for the
  pre-implementation plan.
- [x] (2026-05-10T23:24:32Z) Received explicit user approval to implement the
  planned functionality and keep this ExecPlan current during execution.
- [x] (2026-05-10T23:24:32Z) Added fixture-based architecture tests for
  domain-to-adapter, application-to-adapter, composition-root wiring,
  package-barrel re-export, star re-export, and the current `beatcue` package.
- [x] (2026-05-10T23:24:32Z) Ran the focused red test slice with
  `uv run pytest -q tests/test_architecture_enforcement.py`; it failed during
  collection with `ModuleNotFoundError: No module named 'beatcue.architecture'`
  as expected.
- [x] (2026-05-10T23:24:32Z) Adapted the checker into
  `beatcue.architecture` with BeatCue-specific groups, an explicit
  `beatcue.config` composition-root group, infrastructure-module
  classification, relative import resolution, and package re-export expansion.
- [x] (2026-05-10T23:24:32Z) Ran
  `uv run pytest -q tests/test_architecture_enforcement.py`; all 7 focused
  architecture tests passed.
- [x] (2026-05-10T23:24:32Z) Cleared CodeRabbit concerns on the checker
  milestone, including shared import helpers, public fixture-policy exports,
  docstring detail, explicit fixture bodies, relative-import edge coverage, and
  grouped star re-export lookup.
- [x] (2026-05-10T23:24:32Z) Ran targeted milestone validation:
  `ruff check beatcue/architecture tests/test_architecture_enforcement.py`
  `tests/fixtures/architecture`, `ruff format --check beatcue/architecture`
  `tests/test_architecture_enforcement.py tests/fixtures/architecture`, and
  `uv run pytest -q tests/test_architecture_enforcement.py`; all passed.
- [x] (2026-05-11T00:00:00Z) Added `make check-architecture` and wired
  `make lint` to run the architecture checker after Ruff.
- [x] (2026-05-11T00:00:00Z) Added ADR 003 and updated the developers' guide
  with the enforced rules, Makefile targets, re-export handling, and fixture
  strategy.
- [x] (2026-05-11T00:00:00Z) Ran all required gates with `tee` logs:
  `make check-fmt`, `make lint`, `make typecheck`, `make test`,
  `make markdownlint`, and `make nixie` all passed.
- [x] (2026-05-11T00:00:00Z) Completed the postmortem in
  `Outcomes & Retrospective`.
- [x] (2026-05-11T00:00:00Z) Committed and pushed the completed branch, and
  updated draft PR #8 for review.
- [x] (2026-05-14T00:00:00Z) Addressed code-review comments by tightening
  violation structure assertions, adding valid relative-import and CLI
  coverage, separating imported modules from imported symbols in the checker,
  and expanding uncommon acronyms in this ExecPlan.
- [x] (2026-05-14T00:00:00Z) Ran CodeRabbit and the full required gate set
  for the review follow-up; CodeRabbit reported zero findings and
  `make check-fmt`, `make lint`, `make typecheck`, `make test`,
  `make markdownlint`, and `make nixie` all passed.
- [x] (2026-05-14T00:00:00Z) Split inbound adapter permissions from the
  broader adapter policy so future CLI code may import `beatcue.config` without
  being allowed to import outbound adapters directly.
- [x] (2026-05-14T00:00:00Z) Added fixture coverage for inbound CLI imports of
  the composition root and forbidden direct outbound-adapter imports.
  CodeRabbit reported zero findings, and `make check-fmt`, `make lint`,
  `make typecheck`, and `make test` all passed.
- [x] (2026-05-14T00:00:00Z) Addressed final failed-check warnings by marking
  roadmap item 1.2.2 complete, adding public CLI entrypoint and error-path
  coverage, replacing private re-export helper assertions with public
  `build_reexport_index` checks, and adding Hypothesis property tests for
  import-resolution and policy-classification invariants.

## Surprises & discoveries

- Observation: BeatCue currently has no `src/` directory; the package lives at
  repository root under `beatcue/`. Evidence: `leta files` lists
  `beatcue/__init__.py`, `beatcue/_hello.py`, and `beatcue/pure.py`, while
  `find src tests -maxdepth 4 -type f` reports that `src` does not exist.
  Impact: production checks should use `package_root=Path("beatcue")`; tests
  must use fixtures to model future `domain`, `application`, `adapters`, and
  `config` packages.

- Observation: BeatCue's Makefile already separates `lint`, `typecheck`,
  `test`, `markdownlint`, and `nixie`, and `lint` currently runs only
  `ruff check`. Evidence: `Makefile` defines `lint: ruff` with a single
  `ruff check` recipe. Impact: `check-architecture` can be added as a sibling
  target and included in `lint` without changing the broader gate shape.

- Observation: Episodic's useful reusable pieces are mostly the AST import
  collector, relative import resolver, re-export resolver, result objects, and
  CLI diagnostic flow. Its policy module is intentionally repo-specific.
  Evidence: `episodic/architecture/policy.py` hard-codes groups such as
  `episodic.canonical.domain`, `episodic.api.runtime`, and
  `episodic.worker.runtime`. Impact: BeatCue should keep the mechanism but
  replace the group surface with BeatCue names and fixtures.

- Observation: The red architecture test failed before implementation exactly
  at import time because no `beatcue.architecture` package exists yet. Evidence:
  `/tmp/test-red-beatcue-import-hex-architecture-enforcement.out` contains
  `ModuleNotFoundError: No module named 'beatcue.architecture'`. Impact: The
  planned implementation can proceed against a clear TDD failure.

- Observation: BeatCue needs the policy to classify selected external
  infrastructure modules as a group, not only package-local modules. Evidence:
  `beatcue.domain` is documented as forbidden from importing Rich, Cyclopts,
  OpenCV, librosa, Transformers, Cuprum, and CmdMox, while adapters and CLI
  code may need those packages. Impact: The checker now scans all syntactic
  imports and ignores unclassified standard-library or unrelated modules, while
  the BeatCue policy classifies the named infrastructure packages.

- Observation: CodeRabbit review became temporarily rate-limited after all
  reported checker milestone concerns were fixed. Evidence: The final attempted
  `coderabbit review --agent` returned `rate_limit` with a 2 minute 37 second
  wait after prior passes had reported only two simplifications that were then
  applied and locally retested. Impact: The milestone can be committed after
  local gates pass; the next major milestone will run CodeRabbit again before
  proceeding.

- Observation: The global `make check-fmt` gate currently fails on an unrelated
  existing Markdown code block in
  `docs/complexity-antipatterns-and-refactoring-strategies.md`. Evidence:
  `/tmp/check-fmt-beatcue-import-hex-architecture-enforcement-m1.out` shows
  Ruff would reformat that Markdown file in addition to one new checker file;
  the checker file was then formatted with targeted `ruff format`. Impact:
  Milestone validation used targeted format checking for touched Python and
  fixture files. The unrelated Markdown formatting issue remains for the full
  final gate decision unless later `make fmt` is allowed to change that
  document.

- Observation: The first checker implementation exceeded the ExecPlan's
  production-line tolerance before commit. Evidence:
  `wc -l beatcue/architecture/*.py` reports 844 total production lines under
  `beatcue/architecture`, while the tolerance requires escalation above 700 net
  new production lines. Impact: Implementation is paused until the user
  approves either raising the tolerance or shrinking the checker
  implementation, with the trade-off that shrinking may conflict with some
  CodeRabbit requests for expanded docstrings.

- Observation: The Makefile already builds a virtual environment before test
  and typecheck targets, so `check-architecture` should also depend on
  `build uv`. Evidence: `Makefile` defines `test: build uv $(VENV_TOOLS)` and
  `typecheck: build ty`. Impact: `make lint` now pays the same
  environment-readiness cost before running `python -m beatcue.architecture`,
  which keeps the target reliable in a fresh checkout.

- Observation: A Make prerequisite would run `check-architecture` before the
  `lint` recipe's `ruff check` command, even if the target is listed after
  `ruff` in the dependency list. Evidence: the first `make lint` tee log showed
  `uv run python -m beatcue.architecture` before `ruff check`. Impact: `lint`
  now invokes `$(MAKE) check-architecture` as the second recipe line, so Ruff
  runs first and the architecture gate follows it explicitly.

- Observation: The final CodeRabbit pass reported a minor spelling concern in
  ADR 003, but the current file already uses `behavioural tests` and a search
  of the touched documentation found no `behavior` spelling. Evidence:
  `nl -ba docs/adr-003-hexagonal-architecture-enforcement.md` shows
  `behavioural tests` on line 81, and `grep -R "behavior" ...` returned no
  matches. Impact: the finding was treated as stale after verification rather
  than edited as a no-op.

- Observation: A repeat CodeRabbit pass reported three Markdown blank-line
  concerns that were already satisfied and one valid Oxford-comma concern in
  ADR 003. Evidence:
  `nl -ba docs/adr-003-hexagonal-architecture-enforcement.md` showed blank
  lines around the code fence, table, and `## Goals and non-goals` heading. The
  table row for `adapter` did omit the Oxford comma before
  `and infrastructure`. Impact: the stale blank-line findings were skipped
  after verification, and the table wording was changed to
  `adapter groups, and infrastructure`.

- Observation: Tightening the checker to pass re-export indices explicitly
  initially exceeded Ruff's argument-count limit on `_violations_for_module`.
  Evidence: `make lint` reported `PLR0913` and `PLR0917` for five arguments on
  that helper. Impact: the indices are now bundled in `_ImportIndexes`,
  preserving the narrower `_ModuleContext` while keeping helper signatures
  within local lint limits.

- Observation: The original policy reused the same broad adapter permission
  set for inbound adapters, outbound adapters, and the fallback adapter group.
  Evidence: `inbound_adapter` used `adapter_allowed`, which omitted
  `composition_root` but included `outbound_adapter`. Impact: future
  `beatcue.cli` code importing `beatcue.config` would fail even though the
  design routes CLI wiring through the composition root, while direct CLI
  imports of outbound adapters would be accepted. The inbound group now has its
  own allowed set.

## Decision log

- Decision: Use this ExecPlan as the implementation and postmortem artefact.
  Rationale: the user explicitly requested the plan at
  `docs/execplans/import-hex-architecture-enforcement.md` and allowed the
  postmortem to live in the ExecPlan's `Outcomes & Retrospective`. Date/Author:
  2026-05-10T20:31:41Z / Codex.

- Decision: Keep the first BeatCue trial on standard-library `ast` and do not
  adopt Import Linter, Semgrep, or Astroid during implementation. Rationale:
  the user requested importing and trialling the Episodic mechanism; `ast`
  already covers syntactic imports and re-export expansion without a new
  dependency. Prior art will be assessed in the postmortem rather than added
  prematurely. Date/Author: 2026-05-10T20:31:41Z / Codex.

- Decision: Model BeatCue's `config` package as its own group with permission
  to import all BeatCue groups, rather than adding broad exceptions to domain,
  application, or adapter rules. Rationale: this preserves the documented
  narrow composition-root exception and gives the checker a direct test for
  that design rule. Date/Author: 2026-05-10T20:31:41Z / Codex.

- Decision: Use tests/fixtures packages for future-shape policy coverage while
  the production `beatcue` package remains a skeleton. Rationale: this proves
  intended boundaries without implementing unrelated domain or adapter code.
  Date/Author: 2026-05-10T20:31:41Z / Codex.

- Decision: Treat PR #8 as the existing draft pull request for the whole
  branch and update it after implementation, instead of opening a second PR.
  Rationale: the requested branch already tracks
  `origin/import-hex-architecture-enforcement` and PR #8 exists for this head
  branch. Continuing that PR preserves review history. Date/Author:
  2026-05-10T23:24:32Z / Codex.

- Decision: Add an `infrastructure` group to the policy rather than a separate
  special-case deny list in the checker. Rationale: this keeps all dependency
  direction decisions in policy data and lets adapters allow infrastructure
  while domain and application groups reject it through the same violation path
  as package-local adapter imports. Date/Author: 2026-05-10T23:24:32Z / Codex.

- Decision: Stop before committing the checker milestone because the staged
  production checker is 844 lines, exceeding the 700-line tolerance. Rationale:
  the ExecPlan defines this threshold as an exception trigger. The available
  options are to approve a higher production-line tolerance for this import
  trial, or to shrink the implementation below 700 lines before continuing,
  likely by reducing documentation detail and consolidating helper code.
  Date/Author: 2026-05-10T23:24:32Z / Codex.

- Decision: Keep `check-architecture` as a Makefile target that runs
  `python -m beatcue.architecture` through `uv run`, and make `lint` call that
  target after `ruff check`. Rationale: this follows the repository's Makefile
  style, keeps Ruff as the first lint action, and makes architecture
  enforcement part of the ordinary local quality gate without adding another
  external tool. Date/Author: 2026-05-11T00:00:00Z / Codex.

- Decision: Document architecture enforcement in both ADR 003 and the
  developers' guide. Rationale: the ADR records the accepted architecture
  fitness function, while the developers' guide gives contributors the
  operational commands and fixture guidance they need during implementation.
  Date/Author: 2026-05-11T00:00:00Z / Codex.

- Decision: Keep violation diagnostics at module granularity after splitting
  imported symbols from imported modules. Rationale: the policy classifies
  modules, not symbols. Reporting the owning module avoids duplicate
  symbol-qualified violations while still proving that explicit and star
  package-barrel re-exports cannot hide forbidden adapter dependencies.
  Date/Author: 2026-05-14T00:00:00Z / Codex.

- Decision: Give inbound adapters a dedicated allowed-import set.
  Rationale: inbound CLI adapters are allowed to invoke the composition root
  but must not wire outbound adapters directly. Sharing the broader adapter
  policy hid that distinction and conflicted with the documented future CLI
  design. Date/Author: 2026-05-14T00:00:00Z / Codex.

## Outcomes & retrospective

The implemented outcome matches the planned behaviour. BeatCue now has a
repository-local architecture checker under `beatcue.architecture`, fixture
coverage for the intended future package graph, a production check for the
current `beatcue/` package, an explicit `make check-architecture` target, and
`make lint` runs Ruff before invoking the architecture gate. ADR 003 records
the accepted fitness function, and the developers' guide explains the command,
scope, and fixture strategy.

Reusable without change: the core mechanism transferred well. The useful pieces
were the standard-library `ast` import walk, the split between import
collection and policy classification, the result and violation reporting shape,
the recursive package `__init__.py` re-export expansion, star re-export
handling, and the command-line diagnostic pattern. Those parts needed
adaptation for local names, but not a different technical model.

Episodic-specific parts: the policy was not reusable. Episodic's group names,
module prefixes, and allowed directions describe Episodic packages and worker
runtime choices, not BeatCue. BeatCue also needed explicit handling for
external infrastructure packages such as Rich, Cyclopts, OpenCV, librosa,
Transformers, Cuprum, and CmdMox. Copying Episodic's module groups would have
weakened or misdescribed BeatCue's boundary.

BeatCue's policy surface needed named groups, ordered prefix matching, external
infrastructure classification, a narrow `beatcue.config` composition-root
exception, and a fixture policy for design-first tests. The policy also needed
to distinguish `beatcue.cli` and `beatcue.adapters.inbound` from outbound
adapters while still treating `beatcue.adapters` as a fallback adapter group.

Hard-coded Python policy functions were sufficient for this trial. They are
clear, testable, and cheap while there is one repository and one policy. TOML
or JSON configuration is not needed immediately, but it should be designed
before extracting this into a shared df12/internal tool. A shared tool should
let projects declare package groups, allowed group edges, external module
groups, composition roots, ignored imports, and fixture policies without
editing Python source.

The standard-library `ast` module remained adequate. BeatCue's rule is about
visible source imports, so syntactic analysis is the right level: it finds
`import` and `from ... import ...` statements, relative imports, and package
barrels without executing project code. Dynamic imports, plugin discovery, and
runtime monkeypatching remain out of scope.

Import Linter would reduce maintenance burden for common forbidden-import and
layering rules because it already documents forbidden contracts, layer
contracts, indirect import checks, ignores, and external package support.[^1]
[^2] The trade-off is that BeatCue's trial also needed custom package-barrel
re-export expansion and a local postmortem of the Episodic mechanism. Import
Linter should be evaluated for the shared tool, especially if maintaining graph
traversal and indirect import semantics locally becomes expensive.

Semgrep is useful for precise local import patterns, including Python import
metavariables and import equivalences, but its documented rule model is
pattern-oriented and file-scoped rather than a dependency-graph engine.[^3] It
would probably complement this checker for point rules, not replace the
graph-level policy.

Astroid would help if the checker needed richer inference or import resolution.
It builds on Python abstract syntax trees and provides inference, but its
documentation also exposes the expected trade-off: inference can return
`Uninferable` when static analysis cannot determine a value.[^4] [^5] For
BeatCue's current visible-import rule, that extra dependency and complexity
would not buy enough.

The checker handled the design-first skeleton well once fixtures were used. The
real `beatcue/` package passes today, while the fixture packages prove the
future domain, application, adapter, and composition-root shapes without
creating placeholder production modules. The residual risk is that fixture
coverage must evolve when real packages appear; otherwise the tests may prove
the planned boundary but not every production edge case.

Before trying Prosidy Darn, extract a shared df12/internal tool with these
pieces:

- a stable `ArchitecturePolicy` schema that can load from TOML or JSON;
- reusable AST import collection and relative import resolution;
- reusable package-barrel and star re-export expansion;
- first-class external module groups;
- composition-root exceptions expressed as normal policy groups;
- fixture helpers for synthetic package trees;
- a CLI that emits stable rule IDs and machine-readable diagnostics;
- clear guidance for when to switch to Import Linter rather than extending the
  local mechanism.

The recommended next step is not to add more BeatCue-specific features. It is
to move the mechanism into a small shared package or internal tool, then trial
that extracted interface in Prosidy Darn with BeatCue's policy used as one
configuration example.

## Context and orientation

BeatCue is a Python package under `beatcue/`, with tests under `tests/` and
documentation under `docs/`. The current public API is a smoke function:
`beatcue/__init__.py` imports `hello` from `beatcue/_hello.py`, and
`tests/test_hello.py` asserts that `beatcue.hello()` returns
`"hello from Python"`.

The package is intentionally a skeleton. The design documents describe the
future package boundary:

- `beatcue.domain` contains pure domain values, services, cue entities,
  feature series, and domain-owned port protocols. It must not import adapters,
  CLI code, filesystem adapters, Rich, Cyclopts, OpenCV, librosa, Transformers,
  Cuprum, CmdMox, or other infrastructure.
- `beatcue.application` contains use cases and orchestration. It may import
  domain modules and domain-owned ports.
- `beatcue.adapters` contains infrastructure implementations. It may import
  domain and application contracts plus external infrastructure packages.
- `beatcue.cli` or `beatcue.adapters.inbound.cli` is an inbound CLI adapter.
  It may invoke application services, but it must not wire outbound adapters
  directly unless a design document explicitly says so.
- `beatcue.config` is the composition root. It may import concrete adapters
  and application services to wire dependencies.

In this plan, a "package barrel" means a package `__init__.py` file that
re-exports names from submodules so callers can write imports from the package
root. A "star re-export" means `from module import *` inside such a barrel. The
checker must resolve these re-exports so forbidden imports cannot be hidden
behind a convenient package import.

The Episodic implementation lives in a local sibling repository worktree at
`/home/leynos/.lody/repos/github---leynos---episodic/worktrees/8a6d8653-b5af-4471-961d-33ee0b146a6f/`.
The relevant source files are:

- `episodic/architecture/checker.py`;
- `episodic/architecture/policy.py`;
- `episodic/architecture/reexports.py`;
- `tests/test_architecture_enforcement.py`;
- `tests/features/architecture_enforcement.feature`;
- `tests/steps/test_architecture_enforcement_steps.py`;
- `docs/adr/adr-006-hexagonal-architecture-enforcement.md`.

The reusable mechanism parses Python files with `ast`, collects `import` and
`from ... import ...` statements, resolves package-local relative imports,
expands package re-exports and star re-exports, classifies importer and
imported modules into named groups, and reports dependency-direction violations.

## Plan of work

Stage A is the approval checkpoint. Keep this plan in `DRAFT`, present it to
the user, and wait for explicit approval. Do not rename branches, add tests, or
modify implementation files until approval is received.

Stage B prepares the branch and red tests. Rename the current branch from
`feat/import-hex-enforcement` to `import-hex-architecture-enforcement`. Fetch
or create the remote branch tracking reference as needed, then set upstream
tracking to `origin/import-hex-architecture-enforcement`. Add tests first:
`tests/test_architecture_enforcement.py` should call the checker API against
fixture packages and the production `beatcue` package. Add small fixtures under
`tests/fixtures/architecture/` to prove:

- domain importing an adapter fails;
- application importing an adapter fails;
- application importing domain-owned ports is accepted;
- composition-root wiring is accepted;
- package barrel re-exports cannot hide adapter imports;
- star re-exports cannot hide adapter imports;
- current `beatcue` passes.

Run the focused new tests before implementation and record the expected red
failure in this plan.

Stage C adapts the checker. Add a small package under `beatcue/architecture/`,
expected files:

- `beatcue/architecture/__init__.py` exports the public checker API;
- `beatcue/architecture/__main__.py` runs the CLI entrypoint;
- `beatcue/architecture/cli.py` parses `--package`, `--root`, and
  `--fixture-policy` arguments with `argparse`;
- `beatcue/architecture/checker.py` contains the AST import collector, result
  types, relative import resolver, and scanner;
- `beatcue/architecture/policy.py` contains BeatCue's policy groups and a
  fixture policy;
- `beatcue/architecture/reexports.py` contains the re-export resolver.

Adapt rather than blindly copy. Rename Episodic-specific defaults from
`episodic` to `beatcue`, replace group names and prefixes with BeatCue's
documented package layout, and keep the mechanism dependency-free. The default
BeatCue policy should classify:

- `composition_root`: `beatcue.config`;
- `domain`: `beatcue.domain`;
- `application`: `beatcue.application`;
- `inbound_adapter`: `beatcue.cli` and `beatcue.adapters.inbound`;
- `outbound_adapter`: `beatcue.adapters.outbound`;
- a broad adapter fallback if needed: `beatcue.adapters`.

The allowed directions should be:

- `domain` may import only `domain`;
- `application` may import `domain` and `application`;
- `inbound_adapter` may import `domain`, `application`, `composition_root`,
  and `inbound_adapter`;
- `outbound_adapter` may import `domain`, `application`, and
  `outbound_adapter`;
- `composition_root` may import every group.

If `beatcue.adapters` is used as a fallback group, ensure
`beatcue.adapters.inbound` and `beatcue.adapters.outbound` are listed before it
so specific inbound and outbound rules win. If this broad fallback weakens the
CLI or outbound wiring rule, stop and update the plan before proceeding.

Stage D wires the local quality gate. Add `check-architecture` to `Makefile`
using the existing Makefile style and include it in `lint` after `ruff check`.
The target should run the module entrypoint, probably:

```makefile
check-architecture: build uv ## Verify hexagonal import boundaries
	$(UV_ENV) uv run python -m beatcue.architecture
```

Update `.PHONY` if needed. Keep `make lint` as the user-facing lint gate.

Stage E updates documentation. Add a short ADR such as
`docs/adr-003-hexagonal-architecture-enforcement.md`, because this is an
accepted architecture fitness function. Update `docs/developers-guide.md` to
name `make check-architecture`, explain what it enforces, and clarify that
fixtures model future package boundaries until the production tree exists. Only
update `docs/users-guide.md` if user-facing behaviour changes; this task is
developer-facing, so it probably should not.

Stage F runs validation. Execute gates sequentially and tee long output to
`/tmp`, using filenames that include the branch name:

```bash
make check-fmt 2>&1 | tee /tmp/check-fmt-beatcue-import-hex-architecture-enforcement.out
make lint 2>&1 | tee /tmp/lint-beatcue-import-hex-architecture-enforcement.out
make typecheck 2>&1 | tee /tmp/typecheck-beatcue-import-hex-architecture-enforcement.out
make test 2>&1 | tee /tmp/test-beatcue-import-hex-architecture-enforcement.out
make markdownlint 2>&1 | tee /tmp/markdownlint-beatcue-import-hex-architecture-enforcement.out
make nixie 2>&1 | tee /tmp/nixie-beatcue-import-hex-architecture-enforcement.out
```

If `make check-fmt` fails only because formatting is needed, run
`make fmt 2>&1 | tee /tmp/fmt-beatcue-import-hex-architecture-enforcement.out`
once, then rerun `make check-fmt`. Count this as one focused fix attempt only
if code or documentation changes are needed after formatting.

Stage G completes the postmortem. Update this ExecPlan's `Progress`,
`Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective`.
Answer every required postmortem question and cite the prior-art sources named
below. The conclusion should be specific about what to extract into a shared
df12/internal tool before trying Prosidy Darn.

Stage H commits and publishes. Review `git status --short` and `git diff`. Run
the commit-message workflow using a file-based commit message, stage only the
intended files, and commit after gates pass. Push the renamed branch to origin
and create a draft PR with `gh pr create --draft`. The PR body must mention
this ExecPlan: `docs/execplans/import-hex-architecture-enforcement.md`.

## Concrete steps

Run commands from the repository root:

```bash
cd /home/leynos/.lody/repos/github---leynos---beatcue/worktrees/03438c0b-4acf-4398-ba30-9971fdc63733
```

Before implementation, confirm the branch and clean tree:

```bash
git branch --show-current
git status --short
```

Expected current output before branch rename:

```plaintext
feat/import-hex-enforcement
```

After approval, rename the branch:

```bash
git branch -m import-hex-architecture-enforcement
git fetch origin
git push -u origin import-hex-architecture-enforcement
```

If the remote branch already exists, use the non-destructive Git command that
sets upstream tracking for the local branch. Do not force-push unless the user
explicitly authorizes it.

After adding tests but before implementation, run the focused architecture
tests and expect failures because `beatcue.architecture` does not exist yet:

```bash
make test 2>&1 | tee /tmp/test-red-beatcue-import-hex-architecture-enforcement.out
```

Expected red evidence:

```plaintext
ModuleNotFoundError: No module named 'beatcue.architecture'
```

After implementing, run the focused checker manually:

```bash
UV_CACHE_DIR=.uv-cache UV_TOOL_DIR=.uv-tools uv run python -m beatcue.architecture
```

Expected success output is either empty or a short pass message, with exit
status `0`. A failure prints one or more `ARCH001` diagnostics and exits
non-zero.

Run the full required gates sequentially:

```bash
make check-fmt 2>&1 | tee /tmp/check-fmt-beatcue-import-hex-architecture-enforcement.out
make lint 2>&1 | tee /tmp/lint-beatcue-import-hex-architecture-enforcement.out
make typecheck 2>&1 | tee /tmp/typecheck-beatcue-import-hex-architecture-enforcement.out
make test 2>&1 | tee /tmp/test-beatcue-import-hex-architecture-enforcement.out
make markdownlint 2>&1 | tee /tmp/markdownlint-beatcue-import-hex-architecture-enforcement.out
make nixie 2>&1 | tee /tmp/nixie-beatcue-import-hex-architecture-enforcement.out
```

Create the draft PR after commit and push. Use `gh pr create --draft`, include
the ExecPlan path in the body, and keep the PR summary reviewer-focused.

## Validation and acceptance

Acceptance is behaviour, not file presence.

The architecture checker is accepted when:

- a fixture `domain` package importing an adapter produces an `ARCH001`
  violation and the test fails the package graph;
- a fixture `application` package importing an adapter produces an `ARCH001`
  violation;
- a fixture `application` package importing a domain-owned port passes;
- a fixture `runtime` or `config` package importing application services and
  concrete adapters passes;
- explicit and star package re-exports of adapter symbols still produce an
  `ARCH001` violation when imported from domain or application code;
- running the checker against the real current `beatcue` package passes;
- `make check-architecture` exits `0` on the current package;
- `make lint` runs Ruff and the architecture checker;
- the existing `tests/test_hello.py` smoke test still passes.

Quality criteria:

- Tests: `make test` passes.
- Formatting: `make check-fmt` passes, with `make fmt` used if needed.
- Linting: `make lint` passes and includes `make check-architecture`.
- Type checking: `make typecheck` passes.
- Markdown lint: `make markdownlint` passes.
- Mermaid validation: `make nixie` passes.
- Documentation: the ADR or developers' guide explains the enforced rules,
  the fixture strategy, and the current scope.
- Review hygiene: the final commit is atomic and contains only this task's
  files.

## Idempotence and recovery

All planned edits are additive or narrow replacements. Re-running the checker,
tests, and Makefile gates is safe. If formatting changes Markdown or Python,
inspect the diff before committing.

If a test fixture is wrong, fix the fixture and rerun the focused architecture
test before running the full suite. If the production checker reports a real
BeatCue violation, do not weaken the policy. Inspect the import and either fix
the import direction or escalate if the documented architecture is ambiguous.

If branch rename or upstream setup fails because the remote branch already
exists, stop and inspect `git branch -vv` and `gh pr list` before taking any
destructive action. Do not force-push or delete branches without approval.

If any gate fails for sandbox or network reasons, rerun the same command with
the execution tool's elevated-permission mechanism and record the outcome in
`Surprises & Discoveries`.

## Artifacts and notes

BeatCue repository evidence gathered before drafting:

```plaintext
Current branch: feat/import-hex-enforcement
Current package files: beatcue/__init__.py, beatcue/_hello.py, beatcue/pure.py
Current Makefile lint target: ruff check
Current smoke assertion: beatcue.hello() == "hello from Python"
```

Episodic reusable source reviewed:

```plaintext
episodic/architecture/checker.py
episodic/architecture/policy.py
episodic/architecture/reexports.py
tests/test_architecture_enforcement.py
tests/features/architecture_enforcement.feature
tests/steps/test_architecture_enforcement_steps.py
docs/adr/adr-006-hexagonal-architecture-enforcement.md
```

Prior-art notes from Firecrawl:

- Import Linter forbidden contracts check that one set of modules is not
  imported by another, include descendants by default, can check indirect
  imports, support ignored imports, and can include external packages when
  configured. Source:
  <https://import-linter.readthedocs.io/en/stable/contract_types/forbidden/>.
- Import Linter layers contracts enforce a high-to-low dependency direction,
  include indirect imports, support optional layers, containers, exhaustive
  checks, and same-layer sibling controls. Source:
  <https://import-linter.readthedocs.io/en/stable/contract_types/layers/>.
- Semgrep supports Python import metavariables and import equivalences, but
  its documented matching is primarily pattern and file scoped; the docs also
  note shallow type support and single-file limits for typed metavariables.
  Source: <https://semgrep.dev/docs/writing-rules/pattern-syntax>.
- Astroid provides AST parsing, static analysis, and inference on top of the
  built-in `ast` shape, including `NodeNG.infer()`, but inference can yield
  `Uninferable` when static interpretation cannot follow the code. Sources:
  <https://pylint.pycqa.org/projects/astroid/en/latest/index.html> and
  <https://pylint.pycqa.org/projects/astroid/en/latest/inference.html>.

[^1]: Import Linter forbidden contracts:
    <https://import-linter.readthedocs.io/en/stable/contract_types/forbidden/>.

[^2]: Import Linter layers contracts:
    <https://import-linter.readthedocs.io/en/stable/contract_types/layers/>.

[^3]: Semgrep pattern syntax:
    <https://semgrep.dev/docs/writing-rules/pattern-syntax>.

[^4]: Astroid overview:
    <https://pylint.pycqa.org/projects/astroid/en/latest/index.html>.

[^5]: Astroid inference:
    <https://pylint.pycqa.org/projects/astroid/en/latest/inference.html>.

## Interfaces and dependencies

The implementation should expose these Python interfaces:

```python
from __future__ import annotations

from pathlib import Path

from beatcue.architecture.policy import ArchitecturePolicy


def check_architecture(
    *,
    package_root: Path | str = Path("beatcue"),
    package: str = "beatcue",
    policy: ArchitecturePolicy | None = None,
) -> ArchitectureCheckResult:
    """Check import directions under one package root."""
```

```python
from __future__ import annotations

import dataclasses as dc


@dc.dataclass(frozen=True, slots=True)
class ModuleGroup:
    """One named architecture layer and the groups it may import."""

    name: str
    module_prefixes: tuple[str, ...]
    allowed_groups: frozenset[str]


@dc.dataclass(frozen=True, slots=True)
class ArchitecturePolicy:
    """Dependency-direction policy for a package tree."""

    groups: tuple[ModuleGroup, ...]
    rule_id: str = "ARCH001"
```

```python
from __future__ import annotations


def default_policy() -> ArchitecturePolicy:
    """Return BeatCue's production architecture policy."""


def fixture_policy(package: str) -> ArchitecturePolicy:
    """Return a generic fixture policy used by tests."""
```

The CLI should support:

```bash
python -m beatcue.architecture
python -m beatcue.architecture \
  --package tests.fixtures.architecture.allowed_case \
  --root tests/fixtures/architecture/allowed_case \
  --fixture-policy
```

No runtime dependency should be added. A dev dependency should be added only if
implementation proves it is necessary and the user approves the tolerance
exception.

## Revision note

Initial draft created on 2026-05-10 after reading repository instructions,
BeatCue design documents, the Episodic implementation, and prior-art
documentation. The plan was approved for implementation on 2026-05-10 at
23:24:32Z, progressed through implementation, and is now `COMPLETE`.
