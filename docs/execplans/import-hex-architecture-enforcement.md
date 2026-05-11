# Import Hexagonal Architecture Enforcement

This ExecPlan (execution plan) is a living document. The sections
`Constraints`, `Tolerances`, `Risks`, `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work
proceeds.

Status: IN PROGRESS

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
  future package layout.
  Severity: medium.
  Likelihood: high.
  Mitigation: keep production checks pointed at the current package while using
  small fixture packages under `tests/fixtures/architecture/` for future-shape
  rules.

- Risk: a hard-coded Python policy may become awkward as BeatCue's package
  graph grows.
  Severity: medium.
  Likelihood: medium.
  Mitigation: implement the smallest policy surface now, then answer whether
  TOML or JSON configuration is needed in the postmortem.

- Risk: package barrel re-exports could hide adapter imports if resolution is
  incomplete.
  Severity: high.
  Likelihood: medium.
  Mitigation: adapt Episodic's re-export scanner and add tests for explicit,
  star, nested star, and `__all__`-controlled re-exports as needed.

- Risk: documentation gates may fail because the new ExecPlan and ADR must
  obey the repository Markdown style.
  Severity: low.
  Likelihood: medium.
  Mitigation: wrap Markdown at 80 columns, use labelled code fences, run
  `make markdownlint`, and run `make nixie` if Markdown changes include or
  touch Mermaid diagrams.

- Risk: `make test` or `make typecheck` may require environment writes or
  dependency downloads in a read-only or network-restricted sandbox.
  Severity: medium.
  Likelihood: medium.
  Mitigation: use approved Makefile targets first; if a command fails for
  sandbox or network reasons, rerun it with elevated permissions and record the
  result.

## Progress

- [x] (2026-05-10T20:31:41Z) Read root `AGENTS.md`; no nested `AGENTS.md`
  files exist.
- [x] (2026-05-10T20:31:41Z) Loaded the `execplans`, `leta`, and
  `firecrawl-mcp` skills required by the task and repository instructions.
- [x] (2026-05-10T20:31:41Z) Confirmed the current branch is
  `feat/import-hex-enforcement`, not the main branch.
- [x] (2026-05-10T20:31:41Z) Inspected BeatCue's current skeleton,
  Makefile, `pyproject.toml`, technical design, developers' guide, ADRs, and
  smoke test.
- [x] (2026-05-10T20:31:41Z) Located and reviewed the referenced Episodic
  checker, policy, re-export resolver, tests, BDD feature, BDD steps, and ADR.
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
  `beatcue.config` composition-root group, infrastructure-module classification,
  relative import resolution, and package re-export expansion.
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
  `tests/test_architecture_enforcement.py tests/fixtures/architecture`,
  and `uv run pytest -q tests/test_architecture_enforcement.py`; all passed.
- [ ] Add Makefile architecture gate and wire it into `make lint`.
- [ ] Update documentation.
- [ ] Run all required gates with `tee` logs.
- [ ] Complete the postmortem in `Outcomes & Retrospective`.
- [ ] Commit, push, and create a draft PR.

## Surprises & discoveries

- Observation: BeatCue currently has no `src/` directory; the package lives at
  repository root under `beatcue/`.
  Evidence: `leta files` lists `beatcue/__init__.py`, `beatcue/_hello.py`, and
  `beatcue/pure.py`, while `find src tests -maxdepth 4 -type f` reports that
  `src` does not exist.
  Impact: production checks should use `package_root=Path("beatcue")`; tests
  must use fixtures to model future `domain`, `application`, `adapters`, and
  `config` packages.

- Observation: BeatCue's Makefile already separates `lint`, `typecheck`,
  `test`, `markdownlint`, and `nixie`, and `lint` currently runs only
  `ruff check`.
  Evidence: `Makefile` defines `lint: ruff` with a single `ruff check` recipe.
  Impact: `check-architecture` can be added as a sibling target and included
  in `lint` without changing the broader gate shape.

- Observation: Episodic's useful reusable pieces are mostly the AST import
  collector, relative import resolver, re-export resolver, result objects, and
  CLI diagnostic flow. Its policy module is intentionally repo-specific.
  Evidence: `episodic/architecture/policy.py` hard-codes groups such as
  `episodic.canonical.domain`, `episodic.api.runtime`, and
  `episodic.worker.runtime`.
  Impact: BeatCue should keep the mechanism but replace the group surface with
  BeatCue names and fixtures.

- Observation: The red architecture test failed before implementation exactly
  at import time because no `beatcue.architecture` package exists yet.
  Evidence: `/tmp/test-red-beatcue-import-hex-architecture-enforcement.out`
  contains `ModuleNotFoundError: No module named 'beatcue.architecture'`.
  Impact: The planned implementation can proceed against a clear TDD failure.

- Observation: BeatCue needs the policy to classify selected external
  infrastructure modules as a group, not only package-local modules.
  Evidence: `beatcue.domain` is documented as forbidden from importing Rich,
  Cyclopts, OpenCV, librosa, Transformers, Cuprum, and CmdMox, while adapters
  and CLI code may need those packages.
  Impact: The checker now scans all syntactic imports and ignores unclassified
  standard-library or unrelated modules, while the BeatCue policy classifies
  the named infrastructure packages.

- Observation: CodeRabbit review became temporarily rate-limited after all
  reported checker milestone concerns were fixed.
  Evidence: The final attempted `coderabbit review --agent` returned
  `rate_limit` with a 2 minute 37 second wait after prior passes had reported
  only two simplifications that were then applied and locally retested.
  Impact: The milestone can be committed after local gates pass; the next
  major milestone will run CodeRabbit again before proceeding.

- Observation: The global `make check-fmt` gate currently fails on an unrelated
  existing Markdown code block in
  `docs/complexity-antipatterns-and-refactoring-strategies.md`.
  Evidence: `/tmp/check-fmt-beatcue-import-hex-architecture-enforcement-m1.out`
  shows Ruff would reformat that Markdown file in addition to one new checker
  file; the checker file was then formatted with targeted `ruff format`.
  Impact: Milestone validation used targeted format checking for touched
  Python and fixture files. The unrelated Markdown formatting issue remains
  for the full final gate decision unless later `make fmt` is allowed to change
  that document.

- Observation: The first checker implementation exceeded the ExecPlan's
  production-line tolerance before commit.
  Evidence: `wc -l beatcue/architecture/*.py` reports 844 total production
  lines under `beatcue/architecture`, while the tolerance requires escalation
  above 700 net new production lines.
  Impact: Implementation is paused until the user approves either raising the
  tolerance or shrinking the checker implementation, with the trade-off that
  shrinking may conflict with some CodeRabbit requests for expanded docstrings.

## Decision log

- Decision: Use this ExecPlan as the implementation and postmortem artefact.
  Rationale: the user explicitly requested the plan at
  `docs/execplans/import-hex-architecture-enforcement.md` and allowed the
  postmortem to live in the ExecPlan's `Outcomes & Retrospective`.
  Date/Author: 2026-05-10T20:31:41Z / Codex.

- Decision: Keep the first BeatCue trial on standard-library `ast` and do not
  adopt Import Linter, Semgrep, or Astroid during implementation.
  Rationale: the user requested importing and trialling the Episodic mechanism;
  `ast` already covers syntactic imports and re-export expansion without a new
  dependency. Prior art will be assessed in the postmortem rather than added
  prematurely.
  Date/Author: 2026-05-10T20:31:41Z / Codex.

- Decision: Model BeatCue's `config` package as its own group with permission
  to import all BeatCue groups, rather than adding broad exceptions to domain,
  application, or adapter rules.
  Rationale: this preserves the documented narrow composition-root exception
  and gives the checker a direct test for that design rule.
  Date/Author: 2026-05-10T20:31:41Z / Codex.

- Decision: Use tests/fixtures packages for future-shape policy coverage while
  the production `beatcue` package remains a skeleton.
  Rationale: this proves intended boundaries without implementing unrelated
  domain or adapter code.
  Date/Author: 2026-05-10T20:31:41Z / Codex.

- Decision: Treat PR #8 as the existing draft pull request for the whole
  branch and update it after implementation, instead of opening a second PR.
  Rationale: the requested branch already tracks
  `origin/import-hex-architecture-enforcement` and PR #8 exists for this head
  branch. Continuing that PR preserves review history.
  Date/Author: 2026-05-10T23:24:32Z / Codex.

- Decision: Add an `infrastructure` group to the policy rather than a separate
  special-case deny list in the checker.
  Rationale: this keeps all dependency direction decisions in policy data and
  lets adapters allow infrastructure while domain and application groups reject
  it through the same violation path as package-local adapter imports.
  Date/Author: 2026-05-10T23:24:32Z / Codex.

- Decision: Stop before committing the checker milestone because the staged
  production checker is 844 lines, exceeding the 700-line tolerance.
  Rationale: the ExecPlan defines this threshold as an exception trigger. The
  available options are to approve a higher production-line tolerance for this
  import trial, or to shrink the implementation below 700 lines before
  continuing, likely by reducing documentation detail and consolidating helper
  code.
  Date/Author: 2026-05-10T23:24:32Z / Codex.

## Outcomes & retrospective

This section is intentionally incomplete while the plan is in `DRAFT` status.
At completion, update it with the implemented outcome and the required
postmortem answers:

- Which parts were reusable without change?
- Which parts were Episodic-specific?
- What policy surface did BeatCue need?
- Were hard-coded Python policy functions sufficient, or is TOML or JSON
  configuration needed next?
- Did standard-library `ast` remain adequate?
- Would `astroid`, Semgrep, or Import Linter reduce maintenance burden?
- How well did the checker handle a design-first skeleton repo with future
  package boundaries?
- What should be extracted into a shared df12 or internal tool before trying
  Prosidy Darn?

The postmortem must cite the prior-art sources named in `Artifacts and notes`.

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
  CLI code, filesystem adapters, Rich, Cyclopts, OpenCV, librosa,
  Transformers, Cuprum, CmdMox, or other infrastructure.
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
root. A "star re-export" means `from module import *` inside such a barrel.
The checker must resolve these re-exports so forbidden imports cannot be hidden
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
imported modules into named groups, and reports dependency-direction
violations.

## Plan of work

Stage A is the approval checkpoint. Keep this plan in `DRAFT`, present it to
the user, and wait for explicit approval. Do not rename branches, add tests,
or modify implementation files until approval is received.

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

Stage C adapts the checker. Add a small package under
`beatcue/architecture/`, expected files:

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
- `inbound_adapter` may import `domain`, `application`, and
  `inbound_adapter`;
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
fixtures model future package boundaries until the production tree exists.
Only update `docs/users-guide.md` if user-facing behaviour changes; this task
is developer-facing, so it probably should not.

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

Stage H commits and publishes. Review `git status --short` and `git diff`.
Run the commit-message workflow using a file-based commit message, stage only
the intended files, and commit after gates pass. Push the renamed branch to
origin and create a draft PR with `gh pr create --draft`. The PR body must
mention this ExecPlan:
`docs/execplans/import-hex-architecture-enforcement.md`.

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
  Source:
  <https://semgrep.dev/docs/writing-rules/pattern-syntax>.
- Astroid provides AST parsing, static analysis, and inference on top of the
  built-in `ast` shape, including `NodeNG.infer()`, but inference can yield
  `Uninferable` when static interpretation cannot follow the code. Sources:
  <https://pylint.pycqa.org/projects/astroid/en/latest/index.html> and
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
23:24:32Z. Status changed to `IN PROGRESS`, branch publication progress was
recorded, and implementation may now proceed within the stated tolerances.
