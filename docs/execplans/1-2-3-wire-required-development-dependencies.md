# Wire required development dependencies for BeatCue

This ExecPlan (execution plan) is a living document. The sections `Constraints`,
`Tolerances`, `Risks`, `Progress`, `Surprises & discoveries`, `Decision log`,
and `Outcomes & retrospective` must be kept up to date as work proceeds.

Status: COMPLETE

## Purpose / big picture

Roadmap item 1.2.3 closes the gap between the BeatCue technical design and the
project's dependency manifest. The design (`docs/beatcue-technical-design.md`,
§§14, 16, and 17) declares five dependency groups — `core`, `media`,
`editorial`, `models`, and `dev` — and treats missing optional dependencies as
capability errors reported by `agent-context`, not as import-time crashes. ADR
006 forbids running model code anywhere but the operator's machine, so the
`models` extra remains a declared-but-not-default install.

After this plan lands, a contributor on a fresh checkout can run
`uv sync --group dev && make all` and end up with the development toolchain
plus the `core` runtime extras resolvable, while the optional `media`,
`editorial`, and `models` extras are declared in `pyproject.toml` but absent
from the default environment. The `make all` target must succeed end-to-end, and
`uv run pytest --collect-only -q` must list both the existing unit suites under
`tests/test_*.py` and the behavioural suite in
`tests/test_architecture_package_skeleton_bdd.py`. No domain or adapter
behaviour is introduced.

The plan also closes a subtle gap left by 1.2.1: the Hecate `infrastructure`
group whitelists the prefix `cmdmox`, but the actual importable module name
shipped by the `cmd-mox` distribution is `cmd_mox` (an underscore).
Architecture enforcement must track the import name, not the distribution name.

## Constraints

- Read and follow `AGENTS.md` before changing the repository.
- Use the `leta` skill for code navigation and keep the Leta workspace
  current.
- Use the `hexagonal-architecture` skill when reasoning about which layer
  should be allowed to import which third-party module.
- Use the `execplans` skill and keep this file self-contained and current.
- Do not implement domain value objects, port protocols, application
  services, CLI commands, writer adapters, media adapters, or configuration
  binding in this task. The only production artefacts this plan adds are
  metadata — `pyproject.toml`, `uv.lock`, and Hecate configuration — plus,
  where required, a small regression test that proves the metadata took effect.
- Do not introduce new top-level packages under `beatcue/`.
- Preserve the existing public smoke API: `from beatcue import hello`
  must still work and return `"hello from Python"`.
- Preserve `beatcue.config` as the only production package allowed to
  import both application services and concrete outbound adapters.
- Do not weaken any Hecate rule. The `infrastructure` group must continue
  to model every third-party module whose import would otherwise be silently
  permitted; the rule is being made more accurate, not more permissive.
- Prefer Makefile targets over direct tool commands for gates.
- Run formatting, linting, typechecking, architecture checks, and tests
  sequentially. Do not run those gates in parallel.
- Use `tee` for long gate output with log files under `/tmp`, normalizing the
  branch name so detached HEADs and branch names with slashes produce stable
  file names:

```bash
BRANCH_REF=$(git branch --show-current)
BRANCH_REF=${BRANCH_REF:-$(git rev-parse --short HEAD)}
SAFE_BRANCH_REF=$(printf '%s' "$BRANCH_REF" | tr -c '[:alnum:]._-' '-')
LOG=/tmp/$ACTION-$(basename "$(pwd)")-$SAFE_BRANCH_REF.out
```

- Use `coderabbit review --agent` after each major implementation
  milestone, clear all concerns before moving to the next milestone, and record
  the result here.
- Commit only after the relevant gates pass.

If satisfying the objective requires violating any constraint, stop, document
the conflict in `Decision log`, and ask for direction.

## Tolerances (exception triggers)

- Scope: stop and escalate if implementation touches more than
  approximately six production files. The expected surface is `pyproject.toml`,
  `uv.lock`, the Hecate group block already inside `pyproject.toml`, at most
  one new regression test, and the documentation files listed under
  `Documentation impact`.
- Dependencies: stop and escalate before adding any development tool not
  named in roadmap 1.2.3 (the approved additions are `syrupy` and `cmd-mox`
  only).
- Runtime dependencies: stop and escalate before adding any runtime
  package outside the set named in §6.1 Table 2 of the technical design.
- Resolver failure: if `uv lock` fails because Python 3.14 wheels are
  missing for `librosa`, `OpenTimelineIO`, `torch`, or any of their transitive
  dependencies, stop and escalate. Do not pass
  `--index-strategy unsafe-best-match`, do not pin a downgrade of
  `requires-python`, and do not drop the offending extra silently. The
  escalation must propose either (a) declaring the extra but accepting that
  `pip install beatcue[<extra>]` will fail on 3.14 today, or (b) raising the
  issue with upstream and waiting.
- Ambiguity: if a paste-ready choice is unclear (notably headless vs
  full-fat OpenCV / PySceneDetect, or whether `models` should pin `torch`
  directly), stop and present options rather than guessing.
- Test discovery: if `make all` cannot, after this plan, discover both
  the unit suites and the behavioural suite under `tests/`, stop and escalate.
- Time and iterations: stop and escalate after two focused fix attempts
  on the same failing gate, or after total elapsed wall time exceeds two hours
  for a single milestone.

## Risks

- Risk: `librosa` is currently broken on Python 3.14 (upstream issue
  librosa/librosa#1989 — llvmlite/numba lag; numba 0.65.1 has cp314 wheels but
  librosa pins older numba). Severity: high. Likelihood: high. Impact: a naïve
  `[project.optional-dependencies] media = ["librosa>=0.11"]` would cause
  `uv lock` itself to fail on Python 3.14, because uv solves the union of all
  extras during lock, blocking `make all` end-to-end. Mitigation: marker-gate
  librosa with `; python_full_version < '3.14'` so the resolver excludes it
  from the lock graph on supported Pythons. `pip install beatcue[media]` on
  3.14 then installs only the headless OpenCV stack and PySceneDetect; the
  librosa-dependent code remains declarative-only until upstream catches up.
  Remove the marker once librosa publishes a 3.14-compatible release.

- Risk: `OpenTimelineIO` v0.18.1 has no cp314 wheels (sdist build via
  CMake required). Severity: medium. Likelihood: high. Mitigation: apply the
  same `python_full_version < '3.14'` marker to keep the resolver honest.
  Accept that `pip install beatcue[editorial]` on 3.14 is a no-op today,
  matching the design's post-v1 placement.

- Risk: the `models` extra ultimately depends on a working `torch` 3.14
  wheel set across the supported platforms. Severity: medium. Likelihood:
  medium. Mitigation: apply the `python_full_version < '3.14'` marker to every
  entry in the `models` extra. The whole set is post-v1 per ADR 006 and
  declarative-only on 3.14 until torch publishes cp314 wheels. The marker
  approach also lets the future `models` → `models` + `models-torch` split
  (recorded in the Decision log) happen without breaking declared extras.

- Historical risk: the baseline `inbound_adapter` Hecate group did not allow
  imports from `infrastructure`, but §14 of the design requires the CLI to
  import Cyclopts and Rich (both infrastructure). Severity: medium. Likelihood:
  certain before Stage B. Resolution: Stage B added `"infrastructure"` to
  `inbound_adapter.allowed`. The change is purely additive and matches the
  hexagonal rule that inbound adapters sit at the infrastructure boundary, the
  same as outbound adapters.

- Risk: confusion between the PyPI distribution name `cmd-mox` and the
  Python import name `cmd_mox`. Severity: medium. Likelihood: high. Impact: if
  the Hecate `infrastructure` `prefixes` list keeps `cmdmox` (no underscore),
  the architecture checker silently fails to model the import the first time
  production or test code uses it, and a future adapter could pull `cmd_mox`
  into the domain unnoticed. Mitigation: replace `cmdmox` with `cmd_mox`; add a
  fixture-based architecture test under `tests/fixtures/architecture/` that
  exercises Hecate against an `import cmd_mox` statement, because Hecate does
  not scan `tests/` and a runtime import in a test file cannot prove the rule.
  Add the dist→import mapping as an inline comment in `pyproject.toml`.

- Risk: `scenedetect-headless` and the bare `scenedetect` distribution
  both expose the `scenedetect` Python package and pull conflicting OpenCV
  variants. Severity: medium. Likelihood: low if discipline holds, high if
  someone copy-pastes from upstream docs. Mitigation: pick
  `scenedetect-headless` explicitly, never list bare `scenedetect`, document
  the choice in the Decision log, and add a comment in `pyproject.toml`.

- Risk: `uv.lock` churn becomes large and reviewer-hostile.
  Severity: low. Likelihood: medium. Mitigation: lock once at the end of Stage
  B in a single, isolated commit, with the diff summarised in the commit body.

- Risk: `syrupy` plus `pytest-xdist` `--snapshot-update` disables
  unused-snapshot detection (syrupy issue #535). Severity: low for this plan
  (no snapshot tests yet). Likelihood: high for future work. Mitigation: note
  the constraint in the Decision log so the future CI workflow that runs
  `--snapshot-update` uses `-n0`; do not add such a workflow in this plan.

## Progress

- [x] (2026-06-03T00:00:00+00:00) Loaded `leta`, `python-router`,
  `hexagonal-architecture`, and `execplans` skills.
- [x] (2026-06-03T00:00:00+00:00) Created Leta workspace for this
  worktree.
- [x] (2026-06-03T00:00:00+00:00) Used `firecrawl` to research
  dependency facts for Cuprum, CmdMox, syrupy, PySceneDetect, OpenTimelineIO,
  librosa, OpenCV, Transformers, Cyclopts, Rich, msgspec, and PEP 735.
- [x] (2026-06-03T00:00:00+00:00) Drafted this ExecPlan.
- [x] (2026-06-03T00:00:00+00:00) Ran `logisphere-experts` review on the
  draft. The crew flagged three blockers (resolver behaviour on 3.14, the
  `inbound_adapter` Hecate gap for Cyclopts/Rich, and the misleading scope of
  the `cmd_mox` regression test); all three are folded into Stages B and D and
  the Risks, Decision log, and Validation sections below.
- [x] (2026-06-14T04:52:03+02:00) Received user approval by direct
  implementation request.
- [x] (2026-06-14T04:52:03+02:00) Verified branch is already
  `1-2-3-wire-required-development-dependencies` and the working tree was clean
  before implementation.
- [x] (2026-06-14T04:52:03+02:00) Stage A: baseline `make all`
  passed with 37 tests. Log:
  `/tmp/baseline-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`.
  Pre-edit `uv.lock` size was 394 lines.
- [x] (2026-06-14T04:52:03+02:00) Red stage for the `cmd_mox`
  architecture fixture failed for the intended reason: Hecate returned exit 0
  and printed `architecture check passed` while the test expected a
  `domain -> infrastructure` violation for `cmd_mox`. Log:
  `/tmp/red-cmd-mox-fixture-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`.
- [x] (2026-06-14T04:52:03+02:00) Stage B: extras with
  `python_full_version < '3.14'` markers for librosa, OpenTimelineIO, and the
  `models` set applied; dev additions (`syrupy`, `cmd-mox`) wired with the
  import-name comment; Hecate `infrastructure.prefixes` rename to `cmd_mox`
  plus the new package entries staged for commit; `inbound_adapter.allowed`
  extended with `"infrastructure"`.
- [x] (2026-06-14T04:52:03+02:00) Stage B: architecture-fixture test
  for the renamed `cmd_mox` prefix added under `tests/fixtures/architecture/`
  and exercised from `tests/test_architecture_checker.py`. Runtime smoke check
  (`tests/test_dependency_wiring.py`) added with an honest docstring.
- [x] (2026-06-14T04:52:03+02:00) Stage C: `uv lock` and
  `uv sync --group dev` succeeded cleanly. Logs:
  `/tmp/uv-lock-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`
  and
  `/tmp/uv-sync-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`.
- [x] (2026-06-14T04:52:03+02:00) Focused Stage B checks passed:
  `tests/test_architecture_checker.py::test_hecate_reports_fixture_boundary_violations[domain_imports_cmd_mox-expected_diagnostics1]`
  and `tests/test_dependency_wiring.py`. Full
  `tests/test_architecture_checker.py` also passed with 24 tests. Logs:
  `/tmp/focused-stage-b-2-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`
  and
  `/tmp/architecture-tests-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`.
- [x] (2026-06-14T04:52:03+02:00) Stage D: full `make all`
  passed with 39 tests after lint and typecheck fixes. Log:
  `/tmp/make-all-stage-d-4-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`.
- [x] (2026-06-14T04:52:03+02:00) `uv run pytest --collect-only -q`
  collected 39 tests, including top-level unit suites and
  `tests/test_architecture_package_skeleton_bdd.py`. Log:
  `/tmp/collect-only-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`.
- [x] (2026-06-14T04:52:03+02:00) Standalone
  `make check-architecture` passed. Log:
  `/tmp/check-architecture-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`.
- [x] (2026-06-14T04:52:03+02:00) Markdown gates passed:
  `make markdownlint` and `make nixie`. Logs:
  `/tmp/markdownlint-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`
  and
  `/tmp/nixie-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`.
- [x] (2026-06-14T04:52:03+02:00) Documentation updates landed:
  ADR 009 records the dependency-extra and Python 3.14 marker policy;
  `docs/contents.md`, `docs/developers-guide.md`,
  `docs/beatcue-technical-design.md`, and `docs/roadmap.md` signpost the
  decision.
- [x] (2026-06-14T04:52:03+02:00) Roadmap item 1.2.3 marked done.
- [x] (2026-06-14T04:52:03+02:00) CodeRabbit review found one
  minor issue in `tests/test_dependency_wiring.py`: the smoke test used
  `__import__()` and assertions without failure messages. Replaced those with
  `import_module()` and explicit assertion messages. Focused test passed. Logs:
  `/tmp/coderabbit-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`
  and
  `/tmp/focused-coderabbit-fix-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`.
- [x] (2026-06-14T04:52:03+02:00) Full `make all` passed after
  the CodeRabbit fix with 39 tests. Log:
  `/tmp/make-all-coderabbit-fix-2-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`.
- [x] (2026-06-14T04:52:03+02:00) Second CodeRabbit review found
  two still-valid comments: justify the deliberate fixture `F401` suppression,
  and remove unreachable assertion messages from the dependency smoke test.
  Both were fixed. Focused checks and full `make all` passed with 39 tests.
  Logs:
  `/tmp/coderabbit-2-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`,
  `/tmp/focused-coderabbit-2-fix-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`,
  and
  `/tmp/make-all-coderabbit-2-fix-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`.
- [x] (2026-06-14T04:52:03+02:00) Third CodeRabbit review found
  three still-valid comments: link ADR 006 from ADR 009, parameterize the
  dependency smoke test, and assert on captured version/module return values.
  All were fixed. Focused smoke tests passed with two cases, and full
  `make all` passed with 40 tests. Logs:
  `/tmp/coderabbit-3-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`,
  `/tmp/focused-coderabbit-3-fix-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`,
  and
  `/tmp/make-all-coderabbit-3-fix-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`.
- [x] (2026-06-14T04:52:03+02:00) Fourth CodeRabbit review found
  one still-valid comment: add diagnostic messages to the parameterized smoke
  test assertions. The messages were added. Focused smoke tests passed with two
  cases, and full `make all` passed with 40 tests. Logs:
  `/tmp/coderabbit-4-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`,
  `/tmp/focused-coderabbit-4-fix-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`,
  and
  `/tmp/make-all-coderabbit-4-fix-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`.
- [x] (2026-06-14T04:52:03+02:00) Fifth CodeRabbit review completed
  with zero findings. Log:
  `/tmp/coderabbit-5-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`.
- [x] (2026-06-15T00:00:00+02:00) Follow-up review corrected the
  Pillow Hecate prefix from distribution name `pillow` to import root `PIL`.
  Added `domain_imports_pil` fixture coverage for the standard
  `from PIL import Image` import form. Focused architecture test passed. Log:
  `/tmp/focused-pil-prefix-2-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`.
- [x] (2026-06-16T16:20:28+02:00) Follow-up review verified the
  marker-gating concern remains valid but is tracking work, not a code defect
  in this branch. Opened GitHub issue #18 to track removal of Python 3.14
  markers before roadmap 3.1.3 depends on librosa.
- [x] (2026-06-16T16:20:28+02:00) Captured the per-extra dry-run
  evidence requested by the plan. `core` installs Cuprum and msgspec; `media`
  installs OpenCV headless and PySceneDetect without librosa; `editorial` and
  `models` install no optional packages on Python 3.14. Log:
  `/tmp/dry-run-extras-9bad8eaa-eff1-4139-86d3-65a4afddec5d-1-2-3-wire-required-development-dependencies.out`.

## Surprises & discoveries

- Observation: the existing `inbound_adapter` Hecate group
  (`pyproject.toml` lines 50–53) does not include `"infrastructure"` in its
  `allowed` list, yet design §14 requires the CLI to import Cyclopts and Rich
  (both in the `infrastructure` group). Evidence: current `pyproject.toml`
  `[[tool.hecate.groups]]` `inbound_adapter` block. Impact: a pre-existing gap
  that would break the first CLI commit in 1.3.x. This plan repairs it as part
  of Stage B because the same edit block already extends the `infrastructure`
  prefix list, and leaving the inconsistency behind would invalidate the "make
  all" success criterion the moment any later milestone touched the CLI.

- Observation: `tests/` is not in Hecate's `root_packages = ["beatcue"]`,
  so runtime imports of new dev dependencies from test files do not exercise
  architecture rules. Evidence: `[tool.hecate] root_packages = ["beatcue"]` in
  `pyproject.toml`. Impact: the originally planned
  `tests/test_dependency_wiring.py` claim that "the test proves the rename" was
  wrong. The plan now adds a fixture-based architecture test instead, following
  the pattern already in `tests/fixtures/architecture/`.

- Observation: the fixture Hecate policy builder copied production groups and
  `default_rule_id` but did not copy `include_external_packages = true`.
  Evidence: after adding `domain_imports_cmd_mox`, the focused test still
  printed `hecate: architecture check passed` after `pyproject.toml` had been
  updated, while the dependency smoke test proved `cmd_mox` was installed.
  Impact: existing fixture tests exercised internal BeatCue-like imports but
  could not detect mistakes in third-party infrastructure prefixes. The test
  helper now mirrors production's external-import scanning, and the full
  architecture test module passes with 24 tests.

- Observation: CodeRabbit review caught that the first dependency smoke test
  used the low-level `__import__()` idiom and assertions without diagnostic
  messages. Impact: failures would have been correct but less actionable for a
  contributor diagnosing a miswired dev dependency. The test now uses
  `importlib.import_module()` and explicit assertion messages.

- Observation: a later CodeRabbit pass correctly noted that the explicit
  assertion messages were unreachable because `metadata.version()` and
  `import_module()` raise on failure. Impact: the test is clearer as direct
  calls that let the underlying exception explain the missing distribution or
  import name. The same pass also required a reason on the fixture's
  intentional `F401` suppression.

- Observation: the third CodeRabbit pass asked for a parameterized dependency
  smoke test with assertions on the captured version string and module object,
  and for ADR cross-references to be Markdown links. Impact: the smoke test now
  has one case per dev dependency mapping, and ADR 009 links to ADR 006.

- Observation: the fourth CodeRabbit pass asked for assertion messages on the
  now-reachable smoke-test assertions. Impact: the test keeps explicit value
  checks while reporting which dependency mapping failed.

- Observation: the original Stage B Hecate prefix list used the PyPI
  distribution name `pillow`, but model code imports Pillow through the `PIL`
  package root. Impact: Hecate would not classify `from PIL import Image` as
  infrastructure, leaving the intended domain/application boundary unenforced.
  The infrastructure prefix is now `PIL`, and a fixture test proves that Hecate
  reports the violation. Hecate emits one diagnostic for `PIL` and one for
  `PIL.Image`, so the fixture expects two matching lines.

## Decision log

- 2026-06-03 — Use `[project.optional-dependencies]` for the runtime
  extras (`core`, `media`, `editorial`, `models`) and keep
  `[dependency-groups].dev` for the development toolchain. Rationale: PEP 621
  `optional-dependencies` is the contract library callers use for
  `pip install beatcue[media]`; PEP 735 `[dependency-groups]` is the canonical
  home for tooling-only deps under `uv`. `uv sync --group dev` installs both,
  which matches the Makefile `build` target.

- 2026-06-03 — Use `opencv-python-headless` and `scenedetect-headless`
  together rather than the GUI-enabled variants. Rationale: BeatCue runs as a
  server- and CI-side analysis tool; the headless wheels avoid pulling X11/Qt
  runtime dependencies, and pairing them prevents the same-`cv2`-namespace
  conflict that occurs when `opencv-python` and `opencv-python-headless` are
  co-installed.

- 2026-06-03 — Update Hecate `infrastructure.prefixes` to use
  `cmd_mox` (underscore) instead of `cmdmox`. Rationale: Hecate inspects import
  graphs, so the relevant identifier is the importable module name, not the
  PyPI distribution name. The current `cmdmox` entry would never match.

- 2026-06-03 — Accept that the `editorial` and `models` extras may not
  resolve on Python 3.14 today. Rationale: design Table 2 places them post-v1
  (roadmap 6.x revisits them); declaring them in `pyproject.toml` honours the
  design contract and makes future enablement a metadata-only change. This is
  recorded as a risk, not as a blocker, because v1 work does not depend on
  installing them.

- 2026-06-03 — Note `librosa` 3.14 incompatibility as an active
  upstream defect. Rationale: the project pins `requires-python = ">=3.14"`;
  downgrading the floor would invalidate ADRs and is out of scope. Escalate
  before considering it.

- 2026-06-03 — Document the syrupy + pytest-xdist `--snapshot-update`
  interaction now (syrupy issue #535) so any future CI workflow uses `-n0` when
  updating snapshots, even though no snapshot tests exist yet.

- 2026-06-03 — Gate broken-on-3.14 packages with PEP 508 environment
  markers (`; python_full_version < '3.14'`) rather than declaring them
  unconditionally. Rationale: `uv lock` solves the union of all extras by
  default, so declaring `librosa`, `OpenTimelineIO`, or `torch` unconditionally
  would make the lock — and therefore `make all` — fail on the project's stated
  Python floor. The markers keep the design contract visible in
  `pyproject.toml` while excluding the entries from the resolver graph on 3.14.
  The markers must be removed once upstream ships cp314 wheels; tracked under
  Risks.

- 2026-06-16 — Track marker removal in GitHub issue #18 before roadmap
  3.1.3 starts. Rationale: `librosa` is a v1 media dependency, and the current
  marker is unsatisfiable for every supported Python version while BeatCue
  requires Python 3.14 or newer. This is intentional for lockfile health today,
  but it needs a visible trigger before audio feature loading depends on it.

- 2026-06-16 — Leave `docs/users-guide.md` unchanged. Rationale: this
  milestone changed dependency metadata and contributor setup, but did not add
  or change a user-facing install command or application workflow. The relevant
  maintainer-facing dependency policy is recorded in ADR 009, the technical
  design, and the developers' guide.

- 2026-06-03 — Repair `inbound_adapter.allowed` in Stage B by adding
  `"infrastructure"`. Rationale: design §14 requires the CLI to import Cyclopts
  and Rich, both of which the same plan places in the `infrastructure` group.
  Leaving the current allowed list as-is would ship a known-bad config and
  break the next milestone on its first commit. This is a pre-existing
  inconsistency surfaced by 1.2.3, not a new policy choice.

- 2026-06-03 — Prove the `cmd_mox` prefix rename with a fixture-based Hecate
  test, not a runtime import. Rationale: Hecate does not scan `tests/`, so a
  runtime `import cmd_mox` from a test file cannot exercise the renamed prefix.
  The fixture pattern under `tests/fixtures/architecture/` is the existing
  project mechanism for this kind of assertion; reuse it.

- 2026-06-03 — Treat the headless-OpenCV pairing AND the
  declared-but-not-installable extras policy as a single ADR question (proposed
  ADR 009). Rationale: both decisions outlive this plan and will be
  re-litigated whenever a new dep is added. Recording them only here means they
  disappear when 1.2.3 closes. The ADR is drafted only after user approval of
  this plan.

- 2026-06-03 — Record a future option to split `models` into `models` (CPU
  contract) and `models-torch` (torch only). Rationale: the marker approach
  already isolates torch from the rest of the set, so a future split is
  metadata-only and non-breaking. Not in scope for 1.2.3; noted here so the
  option survives.

## Outcomes & retrospective

Roadmap item 1.2.3 is complete. A fresh checkout can resolve the declared
development environment with `uv sync --group dev`, and `make all` passes with
the dev tooling, the `core` runtime extra, and the Hecate import-name policy in
place. The optional `media`, `editorial`, and `models` extras are declared in
`pyproject.toml`; packages with known Python 3.14 resolver gaps remain
marker-gated until upstream support lands.

The most important implementation lesson was that fixture architecture tests
must mirror production's `include_external_packages = true` setting. Without
that setting, fixture tests can prove BeatCue-to-BeatCue import direction but
cannot prove third-party infrastructure prefix coverage. The new `cmd_mox`
fixture now exercises the exact import name used by the `cmd-mox`
distribution.

The Pillow follow-up adds a second lesson: Hecate prefixes must always be
import roots, not distribution names. The table already identified Pillow's
import root as `PIL`; the enforced prefix now matches that fact.

CodeRabbit review was useful but iterative for the dependency smoke test. The
final shape is a parameterized test that verifies each distribution name maps
to the import name used in Hecate policy, with explicit assertions on the
installed version and imported module object.

## Context and orientation

Repository layout relevant to this plan:

```plaintext
beatcue/
  __init__.py        # public smoke API: hello()
  _hello.py
  pure.py
  domain/            # boundary placeholder (1.2.1)
  application/       # boundary placeholder (1.2.1)
  adapters/          # boundary placeholder (1.2.1)
  config/            # composition root (1.2.1)
tests/
  conftest.py
  features/architecture_package_skeleton.feature
  fixtures/architecture/
  test_architecture_checker.py
  test_architecture_package_skeleton_bdd.py
  test_hello.py
  test_package_skeleton.py
docs/
  beatcue-technical-design.md       # §§6.1, 14, 16, 17
  adr-005-hecate-architecture-enforcement.md
  adr-006-v1-local-only-model-and-privacy-policy.md
  adr-007-v1-beatcue-json-schema.md
  developers-guide.md
  users-guide.md
  roadmap.md
pyproject.toml
uv.lock
Makefile
```

Current `pyproject.toml` state — relevant excerpts as of the baseline:

- `[project] requires-python = ">=3.14"`, `dependencies = []`.
- `[dependency-groups] dev` contains: `hecate` (git pin),
  `hypothesis>=6.152.7`, `pyright`, `pytest`, `pytest-bdd>=8.1.0`, `ruff`,
  `pytest-timeout`, `pytest-xdist`.
- No `[project.optional-dependencies]` table exists.
- `[tool.hecate.groups]` includes an `infrastructure` group whose
  prefixes are `cmdmox`, `cuprum`, `cv2`, `cyclopts`, `librosa`, `rich`,
  `transformers`. This is the import-side allow-list; it is wrong about
  `cmdmox` and incomplete for the post-1.2.3 set.
- `[tool.pytest.ini_options] timeout = 30`.
- `[tool.uv] package = true`.

Makefile contract:

- `make build` is `uv sync --group dev` (via the `.deps` rule), gated
  on `uv` being installed.
- `make all` is `build check-fmt lint typecheck test`.
- `make lint` chains ruff, pylint, and `make check-architecture`
  (`uv run hecate check`).
- `make test` runs `uv run pytest -v -n auto`.

Relevant ADRs:

- ADR 005 — Hecate is the enforcement mechanism; the project's
  architectural rules live in `[tool.hecate]` and are checked in CI.
- ADR 006 — V1 model execution is strictly local; the `models` extra
  must remain optional and is never installed by default in containerised or
  managed environments.
- ADR 007 — BeatCue JSON uses `msgspec.Struct` as its schema
  substrate, so `msgspec` belongs in `core` and `msgspec.json` is already
  aliased by Ruff's import-conventions table.

Research-backed facts driving the pins (retrieval date 2026-06-03):

1. **Cuprum** — PyPI `cuprum` v0.1.0 (released 2025-12-25),
   pure-Python wheel, requires Python >=3.12. Phase-1 maturity (pre-1.0); plan
   for an upgrade pass when 1.0 ships.
2. **CmdMox** — PyPI distribution name is `cmd-mox` (NOT `cmdmox`)
   v0.2.0 (2025-11-26). Importable Python package is `cmd_mox` (underscore).
   Requires Python >=3.11. The pytest plugin auto-registers; the `cmd_mox`
   fixture is injected via entry point. Hecate impact: the current
   `infrastructure` allowed-prefix list contains `cmdmox`. It MUST be changed to
   `cmd_mox` or the architecture rule will silently miss the import.
3. **syrupy** — latest 5.3.1 (2026-05-31). Classifiers 3.10–3.13 but
   the pure-Python wheel installs on 3.14. Pytest-xdist caveat:
   `--snapshot-update` with more than one worker disables unused-snapshot
   detection (syrupy issue #535). Snapshot-update CI must use `-n0`.
4. **PySceneDetect** — PyPI dist `scenedetect` v0.7 (2026-05-03). For
   headless server use BeatCue pins the separate distribution
   `scenedetect-headless` (pulls `opencv-python-headless` instead of
   `opencv-python`). Do NOT also list `opencv-python` — same `cv2` namespace
   conflict.
5. **OpenTimelineIO** — `OpenTimelineIO` v0.18.1 (2025-11-09). No
   cp314 wheel — wheels stop at cp313. Installation on 3.14 needs a CMake sdist
   build. Treat as post-v1.
6. **librosa** — v0.11.0 (2025-03-11). BROKEN on Python 3.14 (open
   issue librosa/librosa#1989: llvmlite/numba lag). Numba 0.65.1 (2026-04) has
   cp314 wheels but librosa pins older numba. Major risk for the `media` extra.
7. **opencv-python / opencv-python-headless** — both 4.13.0.92
   (2026-02-05), cp314 wheels present. Use the headless variant.
8. **Transformers** — v5.9.0 (2026-05-20), classifiers include 3.14.
   Minimum coherent post-v1 `models` extra (CPU-installable): `transformers`,
   `torch` (CPU), `accelerate`, `timm`, `einops`, `pillow`, `sentencepiece`,
   `qwen-vl-utils`. Torch 3.14 wheels are the gating factor.
9. **Cyclopts** — v4.16.1 (2026-05-25), Python 3.14 classified. No
   extras needed for BeatCue's CLI.
10. **Rich** — v15.0.0 (2026-04-12), Python 3.14 classified.
11. **msgspec** — v0.21.1 (2026-04-12), cp314 wheels published. Used
    for BeatCue JSON serialization per ADR 007. Belongs in `core`.
12. **PEP 735 vs PEP 621 under uv** — runtime extras go in
    `[project.optional-dependencies]`; dev-only groups go in
    `[dependency-groups]`. The canonical workflow is
    `uv sync --group dev`, which installs both.

## Plan of work

The plan is broken into four short stages so the change can be reviewed
incrementally and rolled back at any boundary.

**Stage A — Baseline.** Confirm a clean tree, capture baseline gate output, and
prove the current `make all` is green. No production changes.

**Stage B — Wire metadata.** Edit `pyproject.toml` to:

- add the `[project.optional-dependencies]` table (`core`, `media`,
  `editorial`, `models`), applying `; python_full_version < '3.14'` markers to
  librosa (in `media`), OpenTimelineIO (in `editorial`), and every entry in
  `models`;
- extend `[dependency-groups].dev` with `syrupy` and `cmd-mox`, adding an
  inline `# import as cmd_mox` comment beside the `cmd-mox` entry;
- update `[tool.hecate.groups]` `infrastructure.prefixes` to track the
  actual import names (replace `cmdmox` with `cmd_mox`; add `msgspec`,
  `scenedetect`, `opentimelineio`, `torch`, `accelerate`, `timm`, `einops`,
  `PIL`, `sentencepiece`, `qwen_vl_utils`);
- add `"infrastructure"` to `[tool.hecate.groups]` `inbound_adapter.allowed`
  so the CLI can import Cyclopts and Rich in 1.3.x.

Add a fixture-based architecture test under
`tests/fixtures/architecture/domain_imports_cmd_mox/` and extend
`tests/test_architecture_checker.py` so the test would silently pass if the
prefix were misspelt. Add a runtime smoke check
(`tests/test_dependency_wiring.py`) with an honest docstring.

**Stage C — Resolve and sync.** Run `uv lock` followed by
`uv sync --group dev`. If the resolver fails because of a 3.14 wheel gap for
`librosa`, `OpenTimelineIO`, or `torch`, escalate per the `Tolerances` section.
Do not attempt to widen versions, downgrade the Python floor, or pass risky
resolver flags.

**Stage D — Validate, review, document, commit.** Run `make all` end-to-end
under `tee`. Run `uv run pytest --collect-only -q` and confirm both unit and
BDD cases are listed. Run `make check-architecture` and confirm the Hecate
change is clean. Run `coderabbit review --agent`, clear any findings, update
`docs/developers-guide.md`, `docs/users-guide.md` (only if warranted), the
design-doc Table 2 cross-reference if pin choices need a footnote, and finally
mark `docs/roadmap.md` item 1.2.3 done. Commit.

## Concrete steps

### Stage A — baseline

```bash
git branch --show-current
git status --short
ACTION=baseline
LOG=/tmp/$ACTION-$(basename "$(pwd)")-$(git branch --show-current).out
make all 2>&1 | tee "$LOG"

# Record the pre-edit uv.lock size so Stage D can spot runaway churn.
wc -l uv.lock | tee \
    "/tmp/lock-size-pre-$(basename "$(pwd)")-$(git branch --show-current).out"
```

If the baseline `make all` is not green, stop and escalate; this plan assumes a
clean starting point inherited from 1.2.2.

### Stage B — edit `pyproject.toml`

Add the following `[project.optional-dependencies]` table after the existing
`[project]` table:

```toml
[project.optional-dependencies]
# Library values, BeatCue JSON, WebVTT, Cyclopts, Rich, and Cuprum.
core = [
    "cyclopts>=4.16",
    "rich>=15",
    "cuprum>=0.1.0",
    "msgspec>=0.21",
]

# Deterministic analysis with OpenCV, librosa, and PySceneDetect.
# Use the headless OpenCV stack to avoid X11/Qt runtime deps and to
# prevent the same-`cv2` conflict that occurs when both `opencv-python`
# and `opencv-python-headless` are installed.
# Note: librosa is currently broken on Python 3.14 (upstream issue
# librosa/librosa#1989) because llvmlite/numba lag. The PEP 508 marker
# excludes it from the resolver graph on 3.14 so `uv lock` succeeds,
# while keeping the declaration in place. Remove the marker once
# librosa publishes a 3.14-compatible release (tracked under risks).
media = [
    "opencv-python-headless>=4.13",
    "scenedetect-headless>=0.7",
    "librosa>=0.11; python_full_version < '3.14'",
]

# Post-v1 OTIO marker writing. No cp314 wheel for OpenTimelineIO 0.18.1
# at the time of writing; installation on 3.14 currently requires a
# CMake sdist build, so the marker excludes it from the resolver until
# upstream ships cp314 wheels.
editorial = [
    "OpenTimelineIO>=0.18; python_full_version < '3.14'",
]

# Post-v1 local model adapters. ADR 006 forbids remote execution; this
# extra is declared but never installed by default. `torch` has no cp314
# wheel yet and the rest of the stack pulls it in transitively, so the
# whole `models` set is marker-gated to keep `uv lock` solvable today.
# Remove the markers once `torch` ships cp314 wheels.
models = [
    "transformers>=5.9; python_full_version < '3.14'",
    "torch; python_full_version < '3.14'",
    "accelerate; python_full_version < '3.14'",
    "timm; python_full_version < '3.14'",
    "einops; python_full_version < '3.14'",
    "pillow; python_full_version < '3.14'",
    "sentencepiece; python_full_version < '3.14'",
    "qwen-vl-utils; python_full_version < '3.14'",
]
```

Update the existing `[dependency-groups].dev` list to add `syrupy` and
`cmd-mox`. The resulting list:

```toml
[dependency-groups]
dev = [
    "hecate @ git+https://github.com/leynos/hecate.git@46f8c8798e7a80a3a1ab5a13c2a000a4423ffc12",
    "hypothesis>=6.152.7",
    "pyright",
    "pytest",
    "pytest-bdd>=8.1.0",
    "ruff",
    "pytest-timeout",
    "pytest-xdist",
    "syrupy>=5.3",
    "cmd-mox>=0.2",        # import as `cmd_mox` (underscore)
]
```

Update the `infrastructure` Hecate group's `prefixes` to track the importable
module names that production code is allowed to depend on. Both
`opencv-python-headless` and `opencv-python` import as `cv2` (already covered),
and PySceneDetect imports as `scenedetect` regardless of the distribution
variant. The new list:

```toml
[[tool.hecate.groups]]
name = "infrastructure"
prefixes = [
    "accelerate",
    "cmd_mox",       # was "cmdmox"; the importable module name uses an underscore
    "cuprum",
    "cv2",
    "cyclopts",
    "einops",
    "librosa",
    "msgspec",
    "opentimelineio",
    "PIL",
    "qwen_vl_utils",
    "rich",
    "scenedetect",
    "sentencepiece",
    "timm",
    "torch",
    "transformers",
]
# Third-party packages never import BeatCue, so the only meaningful
# inbound edges are the BeatCue-side `allowed` lists on other groups.
allowed = ["infrastructure"]
```

Repair the existing `inbound_adapter` `allowed` list so it can import
infrastructure modules. Cyclopts and Rich are infrastructure under §6.1 of the
design, but §14 requires the CLI to import both, and the current
`inbound_adapter.allowed` list —
`["inbound_adapter", "composition_root", "application", "domain"]` — does not
include `"infrastructure"`. Without this change, the very first CLI commit in
roadmap 1.3.x will fail `make check-architecture`. Update the group to:

```toml
[[tool.hecate.groups]]
name = "inbound_adapter"
prefixes = ["beatcue.cli", "beatcue.adapters.inbound"]
allowed = [
    "inbound_adapter",
    "composition_root",
    "application",
    "domain",
    "infrastructure",
]
```

The change is purely additive — no existing import is forbidden by adding
`infrastructure` to the allowed set — and it matches the hexagonal rule that
inbound and outbound adapters both sit at the infrastructure boundary (see
`docs/developers-guide.md` "Architectural rules"). Record this under the
Decision log.

Add a focused architecture-fixture test that exercises the renamed `cmd_mox`
prefix directly. The runtime-import test alone does not prove the rename because
`tests/` lies outside Hecate's `root_packages = ["beatcue"]` and is therefore
invisible to the architecture checker. Follow the existing fixture pattern under
`tests/fixtures/architecture/`:

1. Add `tests/fixtures/architecture/domain_imports_cmd_mox/domain.py`
   with a single `import cmd_mox` line and the corresponding `__init__.py`.
   This fixture must FAIL Hecate (domain may not import infrastructure).
2. Extend `tests/test_architecture_checker.py` with a test that runs
   Hecate against the fixture and asserts an `ARCH001`-style finding that names
   `cmd_mox`. The test proves that the prefix string matches an actual import
   statement; without the rename it would silently pass.

Optionally also add a runtime smoke check (`tests/test_dependency_wiring.py`)
that calls `importlib.metadata.version("cmd-mox")` and
`importlib.import_module( "cmd_mox")` so reviewers can see the dist-vs-import
mapping documented at the call site. Phrase the docstring as "smoke check that
the cmd-mox distribution installs and exposes the cmd_mox import name"; do NOT
claim the test proves Hecate's rule.

Add a one-line `# import as cmd_mox` comment beside the `cmd-mox>=0.2` entry in
`[dependency-groups].dev` so the mapping is discoverable from `pyproject.toml`
itself, not only from this plan.

### Stage C — resolve and sync

```bash
ACTION=lock
LOG=/tmp/$ACTION-$(basename "$(pwd)")-$(git branch --show-current).out
uv lock 2>&1 | tee "$LOG"

ACTION=sync
LOG=/tmp/$ACTION-$(basename "$(pwd)")-$(git branch --show-current).out
uv sync --group dev 2>&1 | tee "$LOG"
```

If `uv lock` fails on the `core + dev` set, stop and escalate. The
`python_full_version < '3.14'` markers on librosa, OpenTimelineIO, and the
`models` set should keep those entries out of the resolver graph entirely, so a
failure here points to an unexpected upstream regression — diagnose before
retrying. Do not pass `--index-strategy unsafe-best-match`, do not relax
`requires-python`, and do not drop entries silently.

### Stage D — validate, review, document, commit

```bash
ACTION=make-all
LOG=/tmp/$ACTION-$(basename "$(pwd)")-$(git branch --show-current).out
make all 2>&1 | tee "$LOG"

ACTION=collect
LOG=/tmp/$ACTION-$(basename "$(pwd)")-$(git branch --show-current).out
uv run pytest --collect-only -q 2>&1 | tee "$LOG"

ACTION=arch
LOG=/tmp/$ACTION-$(basename "$(pwd)")-$(git branch --show-current).out
make check-architecture 2>&1 | tee "$LOG"

# Machine-checkable evidence for the extras behaviour on 3.14.
for extra in core media editorial models; do
    ACTION="dry-install-${extra}"
    LOG=/tmp/$ACTION-$(basename "$(pwd)")-$(git branch --show-current).out
    uv pip install --dry-run -e ".[${extra}]" 2>&1 | tee "$LOG"
done

# Final uv.lock size check; compare against the pre-edit baseline.
wc -l uv.lock | tee \
    "/tmp/lock-size-post-$(basename "$(pwd)")-$(git branch --show-current).out"

coderabbit review --agent
```

Document the dry-install transcripts in the commit body so reviewers can
confirm at a glance that `media` installs the headless OpenCV stack without
librosa, and that `editorial` and `models` produce empty install plans on 3.14.

Documentation edits, then commit.

## Validation and acceptance

Success is exactly the roadmap statement: `make all` installs the package and
can discover the empty unit and behavioural test suites. Concretely, all of the
following must hold after the change:

1. From a fresh checkout: `uv sync --group dev` succeeds. `make all`
   exits zero. The captured `/tmp/make-all-*.out` log shows `build`,
   `check-fmt`, `lint` (including `check-architecture`), `typecheck`, and
   `test` all passing.
2. `uv run pytest --collect-only -q` lists, at minimum, the existing
   unit tests under `tests/test_hello.py`, `tests/test_package_skeleton.py`,
   `tests/test_architecture_checker.py`, and the BDD scenarios discovered via
   `tests/test_architecture_package_skeleton_bdd.py` and the
   `tests/features/architecture_package_skeleton.feature` file.
3. `make check-architecture` exits zero against the production tree, and
   the new fixture-based test from Stage B asserts that Hecate raises an
   `ARCH001`-style finding for `import cmd_mox` from a domain fixture. The
   fixture-based assertion is the test that proves the `cmd_mox` prefix rename
   actually matches an import statement; without it the prefix could be
   misspelt and silently miss every real-world import.
4. The runtime smoke test `tests/test_dependency_wiring.py` passes, with
   its docstring scoped to "the cmd-mox distribution installs and the cmd_mox
   import name resolves on this Python".
5. `uv pip install --dry-run -e ".[core]"` succeeds on Python 3.14 in a
   scratch environment and lists `cyclopts`, `rich`, `cuprum`, and `msgspec`.
   `uv pip install --dry-run -e ".[media]"` succeeds and lists
   `opencv-python-headless` and `scenedetect-headless` but NOT `librosa` (the
   environment marker excludes it on 3.14).
   `uv pip install --dry-run -e ".[editorial]"` and
   `uv pip install --dry-run -e ".[models]"` succeed with empty install plans
   on 3.14 (marker-gated). Capture each transcript under `/tmp` so the "no
   install on 3.14" claim is machine-checkable, not verbal.
6. `coderabbit review --agent` reports no actionable findings.
7. `docs/roadmap.md` 1.2.3 is marked done only after steps 1–6 hold.

## Idempotence and recovery

- `uv lock` and `uv sync --group dev` are idempotent: re-running them
  on an already-synced tree is a no-op modulo timestamps.
- The Hecate prefix rename is a metadata-only edit; re-running
  `hecate check` after the edit is idempotent.
- Rollback is `git checkout -- pyproject.toml uv.lock` followed by
  `make build` to restore the previous environment. The new test file, if
  added, can be removed with a single `git rm` (the test does not import any
  production module, so the production tree is unaffected).
- If the resolver gets into a half-locked state, delete `.venv` and
  `.deps`, then re-run `make build`.

## Artifacts and notes

Captured logs under
`/tmp/$ACTION-$(basename "$(pwd)")-$(git branch --show-current).out` for each of
`baseline`, `lock`, `sync`, `make-all`, `collect`, and `arch`. The
`coderabbit review --agent` transcript is linked from the `Progress` section
once it lands.

## Interfaces and dependencies

| PyPI dist                | Import name      | Pin        | Group       | Notes                                                                       |
| ------------------------ | ---------------- | ---------- | ----------- | --------------------------------------------------------------------------- |
| `cyclopts`               | `cyclopts`       | `>=4.16`   | `core`      | 3.14-classified (finding 9).                                                |
| `rich`                   | `rich`           | `>=15`     | `core`      | 3.14-classified (finding 10).                                               |
| `cuprum`                 | `cuprum`         | `>=0.1.0`  | `core`      | Pre-1.0; revisit on 1.0 (finding 1).                                        |
| `msgspec`                | `msgspec`        | `>=0.21`   | `core`      | cp314 wheels published (finding 11); required by ADR 007.                   |
| `opencv-python-headless` | `cv2`            | `>=4.13`   | `media`     | Headless, server-friendly (finding 7). Do not also list `opencv-python`.    |
| `scenedetect-headless`   | `scenedetect`    | `>=0.7`    | `media`     | Pairs with headless OpenCV (finding 4).                                     |
| `librosa`                | `librosa`        | `>=0.11`   | `media`     | Marker-gated `< 3.14` (finding 6); declared per design.                     |
| `OpenTimelineIO`         | `opentimelineio` | `>=0.18`   | `editorial` | Marker-gated `< 3.14` (finding 5); post-v1.                                 |
| `transformers`           | `transformers`   | `>=5.9`    | `models`    | Marker-gated `< 3.14` to match the rest of the set (finding 8).             |
| `torch`                  | `torch`          | (unpinned) | `models`    | Marker-gated `< 3.14`; no cp314 wheel yet (finding 8).                      |
| `accelerate`             | `accelerate`     | (unpinned) | `models`    | Marker-gated `< 3.14`; post-v1 `models` set (finding 8).                    |
| `timm`                   | `timm`           | (unpinned) | `models`    | Marker-gated `< 3.14`; post-v1 `models` set (finding 8).                    |
| `einops`                 | `einops`         | (unpinned) | `models`    | Marker-gated `< 3.14`; post-v1 `models` set (finding 8).                    |
| `pillow`                 | `PIL` (`pillow`) | (unpinned) | `models`    | Marker-gated `< 3.14`; imaging dep for Transformers (finding 8).            |
| `sentencepiece`          | `sentencepiece`  | (unpinned) | `models`    | Marker-gated `< 3.14`; tokeniser dep (finding 8).                           |
| `qwen-vl-utils`          | `qwen_vl_utils`  | (unpinned) | `models`    | Marker-gated `< 3.14`; Qwen helper (finding 8).                             |
| `syrupy`                 | `syrupy`         | `>=5.3`    | `dev`       | Pure-Python wheel installs on 3.14 (finding 3); xdist caveat noted.         |
| `cmd-mox`                | `cmd_mox`        | `>=0.2`    | `dev`       | Dist vs import-name mismatch — Hecate prefix MUST be `cmd_mox` (finding 2). |

_Table 1: Dependencies added by this plan, grouped by extra._

Hecate `infrastructure` group prefix changes: `cmdmox` → `cmd_mox`; add
`accelerate`, `einops`, `msgspec`, `opentimelineio`, `PIL`, `qwen_vl_utils`,
`scenedetect`, `sentencepiece`, `timm`, `torch`. The existing entries `cuprum`,
`cv2`, `cyclopts`, `librosa`, `rich`, `transformers` remain.

## Documentation impact

- `docs/developers-guide.md` — add (or extend) a "Subprocess tooling"
  section that names CmdMox, calls out the `cmd-mox` (dist) → `cmd_mox`
  (import) mapping, and points to the pytest plugin's `cmd_mox` fixture.
  Mention the dependency-group layout (`core`, `media`, `editorial`, `models`,
  `dev`) and the `uv sync --group dev` entry point.
- `docs/users-guide.md` — touch only if a library-caller-facing
  install command needs to be documented (for example
  `pip install beatcue[media]`). If the user-facing surface for v1 is still
  CLI-only and CLI installation is unchanged, leave this file alone and record
  that decision here.
- `docs/beatcue-technical-design.md` — add a Table 2 footnote noting
  the current Python 3.14 wheel gaps for `librosa`, `OpenTimelineIO`, and
  `torch`, the marker-gating mitigation, and the headless-OpenCV choice. The
  design itself does not change.
- `docs/roadmap.md` — mark item 1.2.3 done ONLY after validation
  passes.
- ADR escalation: the logisphere review recommended lifting two coupled
  decisions to a single new ADR — the headless-OpenCV/scenedetect-headless
  pairing AND the "declared-but-not-installable extras during Python-version
  transition windows" policy. After user approval of this plan, draft ADR 009
  (proposed title: "Declared-but-not-installable extras and headless
  media-library coupling"), reference it from §6.1 of the design doc, and link
  to it from the Decision log. The ADR draft is out of scope for the
  metadata-only milestone but should land in the same PR if reviewers want the
  policy captured before the next milestone.
