# Record the v1 local-only model and privacy policy

This ExecPlan (execution plan) is a living document. The sections `Constraints`,
 `Tolerances`, `Risks`, `Progress`, `Surprises & Discoveries`, `Decision Log`,
and `Outcomes & Retrospective` must be kept up to date as work proceeds.

Status: IN PROGRESS

The user approved implementation on 2026-05-20. Proceed milestone by milestone
within the constraints and tolerances in this plan.

## Purpose / Big Picture

Roadmap item 1.1.3 closes the local-only privacy decision in the phase 1
architecture ratification work. BeatCue v1 is already described as a
deterministic, local analysis package, but later model-adapter tasks need a
clear contract for what happens when a caller asks for a remote backend before
BeatCue has a privacy and credentials design.

After this plan is approved and implemented, a reviewer should be able to open
the documentation and see one durable policy: BeatCue v1 does not execute
models remotely, does not persist remote API credentials, and fails clearly
when a requested remote backend is not present in the configured capability
set. The observable outcome is documentation alignment and a testable future
implementation contract, not remote model code.

## Constraints

- Do not implement production model adapters, remote inference clients,
  credential storage, command-line interface (CLI) flags, package dependency
  changes, network calls, or model download behaviour in this task. This task
  records the policy and implementation contract.
- Preserve the v1 boundary in
  `docs/beatcue-technical-design.md` section 3.1: v1 is deterministic cue
  extraction for single-scene or single-shot videos. Remote model execution is
  post-v1 work.
- Preserve the security rule in `docs/beatcue-technical-design.md` section 19:
  profiles may store model names and default output settings, but not API keys.
- Preserve the deferred decision in `docs/beatcue-technical-design.md` section
  21: remote model execution and remote adapters require a future privacy and
  credentials design before any implementation can opt in.
- Preserve the hexagonal architecture rule from the `hexagonal-architecture`
  skill: the domain owns ports and capability concepts, while Hugging Face,
  Ollama, HTTP clients, tokens, credentials, and remote-service objects stay in
  adapters or future composition-root code.
- Treat the future configured capability set as an explicit contract. A
  backend being available must not be inferred from a package name alone,
  because the same tool family can support both local and remote execution.
- Use the next available ADR number at implementation time. The current
  repository has `docs/adr-001-*.md` through `docs/adr-005-*.md`, with two
  historical `adr-003` files, so the expected file is
  `docs/adr-006-v1-local-only-model-and-privacy-policy.md` unless a new ADR
  lands first.
- Follow `docs/documentation-style-guide.md`: British English with Oxford
  spelling, sentence-case headings, wrapped prose, fenced code blocks with
  language identifiers, ADR naming conventions, table captions, and required
  ADR sections.
- Signpost the relevant skills in implementation notes and progress:
  `execplans`, `leta`, `hexagonal-architecture`, `firecrawl-mcp`,
  `en-gb-oxendict-style`, `commit-message`, and `pr-creation`.
- Use Makefile targets for quality gates. Run gates sequentially and write logs
  under `/tmp`; do not run tests, linters, formatting, or format checks in
  parallel.
- Use `coderabbit review --agent` after each major implementation milestone,
  record concerns in this plan, and clear all concerns before moving on.
- Commit each approved implementation milestone only after its required gates
  pass.

If satisfying the objective requires violating a constraint, stop, document the
conflict in `Decision Log`, and ask for direction.

## Tolerances

- Scope: if implementation requires modifying more than six files besides this
  ExecPlan, stop and ask whether roadmap item 1.1.3 should widen beyond
  decision ratification.
- Size: if the net documentation change exceeds 900 lines outside this
  ExecPlan, stop and ask whether to split the work.
- Dependencies: if the decision requires adding or changing Python
  dependencies now, stop and ask whether package wiring should move to roadmap
  item 1.2.3 or a later model-adapter task.
- Interface: if implementation would change public Python APIs, CLI behaviour,
  persisted output formats, BeatCue JSON fields, or `agent-context` payload
  shape immediately, stop and ask for approval.
- Capability contract: if implementation cannot express remote-backend failure
  without inventing new runtime code in this task, record the future contract
  in the ADR and defer code to the package-skeleton or model-adapter task.
- ADR numbering: if another `docs/adr-006-*.md` appears before implementation,
  use the next available ADR number and record the change in `Decision Log`.
- Validation: if any required gate fails after two focused fix attempts, stop,
  record the failing command and log path, and ask for direction.
- Review: if `coderabbit review --agent` raises concerns that require
  implementation beyond the tolerances above, stop and ask for direction.
- Ambiguity: if multiple valid policy forms materially change the outcome,
  such as banning all local HTTP adapters versus permitting localhost-only
  adapters, stop and present the trade-offs. The default path is to permit only
  explicitly configured local capabilities for v1.

## Risks

- Risk: Documentation could imply that remote model execution is implemented or
  supported in v1. Severity: high. Likelihood: medium. Mitigation: phrase the
  ADR, users' guide, and design signposts as a local-only v1 policy and a
  future failure contract, not as new runtime support.

- Risk: "Remote backend" could be too vague because some open-source tools use
  both local and hosted endpoints. Severity: medium. Likelihood: high.
  Mitigation: define backend locality by configured capability and endpoint,
  not by library name. Ollama is the concrete prior-art example: its API can
  target `http://localhost:11434/api` or `https://ollama.com/api`.

- Risk: The phrase "configured capability set" is not yet a concrete runtime
  type in the package. Severity: medium. Likelihood: high. Mitigation: record
  the required future behaviour in the ADR and technical design. Defer code
  until the package skeleton and model-adapter tasks own the actual types.

- Risk: Expanding `agent-context` with backend-specific details now could
  create an externally visible compatibility contract before the package
  skeleton exists. Severity: medium. Likelihood: medium. Mitigation: document
  the required future capability semantics without changing the payload shape
  in this documentation-only task unless an approved implementation decision
  says otherwise.

- Risk: ADR numbering was already imperfect because two ADR 003 files existed.
  Severity: low. Likelihood: medium. Mitigation: use the next available number
  at implementation time, expected to be ADR 006, and record the numbering
  decision in this plan.

- Risk: A local-only policy could be weakened by implicit model downloads,
  telemetry, or credential reuse from third-party libraries. Severity: high.
  Likelihood: medium. Mitigation: require the ADR to state that future local
  model adapters must use explicit local-file or offline controls and must not
  silently send credentials or media-derived data to remote services.

## Progress

- [x] (2026-05-19 11:17Z) Loaded the `leta`,
  `hexagonal-architecture`, `execplans`, `firecrawl-mcp`,
  `en-gb-oxendict-style`, `commit-message`, and `pr-creation` skills relevant
  to this planning task.
- [x] (2026-05-19 11:17Z) Added this repository to the Leta workspace.
- [x] (2026-05-19 11:17Z) Renamed the branch to
  `1-1-3-record-local-only-policy-for-v1`. The matching remote branch does not
  exist yet; tracking will be set by `git push -u` after the plan commit.
- [x] (2026-05-19 11:17Z) Created the `context_pack` pack
  `beatcue-1-1-3-local-only-plan` for the Wyvern agent team.
- [x] (2026-05-19 11:17Z) Used two Wyvern agents to review the project docs,
  completed ExecPlans, quality gates, CodeRabbit workflow, and planning risks.
- [x] (2026-05-19 11:17Z) Used Firecrawl to review prior art in Hugging Face
  offline model loading and Ollama local versus cloud API endpoints.
- [x] (2026-05-19 11:17Z) Drafted this ExecPlan at
  `docs/execplans/1-1-3-record-local-only-policy-for-v1.md`.
- [x] (2026-05-19 11:23Z) Ran `coderabbit review --agent` on the draft plan.
  The first run reported one valid trivial wording issue, which was fixed.
- [x] (2026-05-19 11:28Z) Reran `coderabbit review --agent`; it completed
  with zero findings.
- [x] (2026-05-19 11:31Z) Validated the draft plan with `make markdownlint`,
  `make nixie`, `make check-fmt`, `make typecheck`, `make lint`, and
  `make test`; all gates passed with logs under `/tmp`.
- [x] (2026-05-19 11:34Z) Committed the draft plan.
- [x] (2026-05-19 11:36Z) Pushed the branch and created draft pull request
  11 for plan review.
- [x] (2026-05-20 00:00Z) Received explicit user approval to implement this
  plan.
- [x] (2026-05-20 00:08Z) Implemented milestone 1 by adding
  `docs/adr-006-v1-local-only-model-and-privacy-policy.md`.
- [x] (2026-05-20 00:14Z) Ran `coderabbit review --agent` after milestone 1;
  it completed with zero findings.
- [x] (2026-05-20 00:20Z) Implemented milestone 2 by signposting ADR 006 from
  the technical design, developers' guide, and users' guide.
- [x] (2026-05-20 00:26Z) Ran `coderabbit review --agent` after milestone 2;
  it completed with zero findings.
- [x] (2026-05-20 00:28Z) Implemented milestone 3 by marking roadmap item
  1.1.3 done and citing ADR 006 as the durable decision record.
- [x] (2026-05-20 00:36Z) Ran final validation gates sequentially with logs
  under `/tmp`: `make markdownlint`, `make nixie`, `make check-fmt`,
  `make lint`, `make typecheck`, and `make test` all passed.
- [x] (2026-05-20 00:42Z) Ran a final `coderabbit review --agent` on the
  complete implementation. It reported one trivial process finding to verify
  Markdown formatting and linting for ADR 006.
- [x] (2026-05-20 00:44Z) Verified ADR 006 table formatting and reran
  `make markdownlint`; the gate passed with zero errors.
- [x] (2026-05-20 00:53Z) Reran `coderabbit review --agent`; the first rerun
  hit a recoverable rate limit, and the retry completed with zero findings.
- [x] (2026-05-20 00:55Z) Prepared the approved implementation for commit
  after final Markdown lint verification.

## Surprises & Discoveries

- Observation: `docs/beatcue-technical-design.md` already says v1 runs local
  analysis only and that remote model execution is out of scope until a future
  privacy and credentials design exists. Impact: implementation should ratify
  and make the failure contract concrete rather than introduce a new policy.

- Observation: `docs/roadmap.md` item 1.1.3 names the success condition as
  clear failure when a requested remote backend is not part of the configured
  capability set. Impact: the ADR must say more than "remote execution is
  deferred"; it must specify a future capability-mismatch error contract.

- Observation: Hugging Face tooling exposes local/offline controls such as
  `local_files_only=True` in Transformers and `HF_HUB_OFFLINE=1` in
  `huggingface_hub`. Impact: future local model adapters have established prior
  art for explicit offline operation and should not rely on best-effort network
  avoidance.

- Observation: Hugging Face Hub also documents token and implicit-token
  environment variables. Impact: the privacy policy must explicitly forbid v1
  profiles from storing API keys and should warn future remote-adapter work to
  design credential handling before implementation.

- Observation: Ollama documents a localhost API base URL and a cloud API base
  URL for the same API family. Impact: BeatCue should classify model execution
  by configured capability and endpoint locality, not by adapter brand or
  protocol shape.

- Observation: The Wyvern team found no hard contradiction between roadmap
  item 1.1.3 and the current design, but found a gap around backend-specific
  failure semantics. Impact: the implementation should add a small ADR and
  focused design signposts, not broad rewrites.

- Observation: The first CodeRabbit review reported one trivial but valid
  wording issue: "roadmap 6.1" should be "roadmap item 6.1". Impact: the
  wording was corrected before running the validation gates.

- Observation: The milestone 1 CodeRabbit review completed with zero findings
  after ADR 006 was added. Impact: implementation proceeded to documentation
  signposts.

- Observation: The milestone 2 CodeRabbit review completed with zero findings
  after the technical design, developers' guide, and users' guide signposted
  ADR 006. Impact: implementation proceeded to the roadmap update.

- Observation: `make fmt` returned non-zero after touching unrelated Markdown
  files because the repository-wide fixer surfaced existing long-table
  line-length reports in older documents. The unrelated formatter edits were
  restored, and the branch changes passed `make markdownlint` and
  `make check-fmt`. Impact: no unrelated Markdown churn is included in the
  implementation.

- Observation: The final CodeRabbit review reported a trivial process concern
  asking for Markdown formatting and linting on ADR 006. ADR 006 rendered with
  the expected title and table, and `make markdownlint` passed with zero
  errors. Impact: the concern was addressed through validation evidence rather
  than a content change.

- Observation: The first final CodeRabbit rerun was rate limited with a
  recoverable wait. A retry after the requested delay completed with zero
  findings. Impact: all CodeRabbit concerns are cleared.

## Decision Log

- Decision: Draft this as a pre-implementation ExecPlan only.
  Rationale: the user explicitly said the plan must be approved before it is
  implemented, and the `execplans` skill requires an approval gate.

- Decision: Expected ADR path is
  `docs/adr-006-v1-local-only-model-and-privacy-policy.md`. Rationale: ADR 005
  was the current highest unique ADR number. Two ADR 003 files existed, so
  implementation should use the next available number instead of renumbering
  history.

- Decision: Treat local-only policy as a capability contract rather than a
  library blacklist. Rationale: prior art shows the same model tooling can
  support local cached execution, local HTTP serving, and hosted endpoints. The
  policy must make the configured capability set explicit.

- Decision: Do not require property tests, snapshot tests, behavioural tests,
  or end-to-end tests for this documentation-only implementation. Rationale:
  roadmap item 1.1.3 records a decision and contract. The plan must require
  those test types when later runtime code makes the policy observable, but
  this documentation change can be validated through Markdown, architecture,
  type, lint, and test gates.

- Decision: Use ADR 006 for the local-only model and privacy policy.
  Rationale: no new ADR 006 existed when implementation began, so the expected
  next available ADR number remained valid.

## Implementation Plan

Implementation must begin only after explicit approval. Once approved, update
this plan's status to `IN PROGRESS`, add a progress entry with the approval
timestamp, and proceed milestone by milestone.

### Milestone 1: Ratify the policy in an ADR

Create `docs/adr-006-v1-local-only-model-and-privacy-policy.md`, or the next
available ADR number if ADR 006 is already taken. The ADR should follow
`docs/documentation-style-guide.md` and include these decisions:

- BeatCue v1 performs local analysis only.
- Remote model execution, hosted inference, network inference endpoints, and
  remote model adapters are out of scope until a separate privacy and
  credentials design exists.
- Profiles may name local models and defaults, but must not store API keys,
  bearer tokens, session cookies, or remote service credentials.
- Future model adapters must report their capabilities explicitly. A requested
  remote backend that is absent from the configured capability set must fail
  before inference with a clear capability error.
- Future local model adapters must use explicit offline or local-file controls
  where the underlying library provides them.
- Local HTTP endpoints, such as localhost model servers, are not automatically
  permitted merely because they use loopback. They require an explicit local
  capability entry and must not be generalized into remote execution.

The ADR should consider at least these options:

1. Keep the current informal design wording only.
2. Record a strict v1 local-only ADR with explicit capability failure.
3. Permit remote model execution behind experimental configuration now.

Choose option 2 unless implementation discovers a documented constraint that
requires escalation.

Acceptance for this milestone:

- The ADR is `Accepted` and dated with the implementation date.
- The ADR states the local-only v1 policy and remote-backend failure contract.
- The ADR explains why remote credentials and privacy require a later design.
- The ADR does not imply that remote execution is implemented.

Run `coderabbit review --agent` after this milestone and clear concerns before
continuing.

### Milestone 2: Add documentation signposts

Update `docs/beatcue-technical-design.md` to reference the new ADR from the v1
boundary, semantic annotation, security and privacy, failure modes, and
deferred decisions where concise signposts are needed. Keep the edits narrow.
The most important change is the failure behaviour:

```plaintext
Requested remote backend is not configured: fail before inference with a
capability error that names the unsupported backend and points to the local-only
v1 policy.
```

Update `docs/developers-guide.md` to document the internal convention for
future model-adapter authors:

- model backends must advertise locality and capability explicitly;
- profiles must not persist secrets;
- adapters must not silently fall back from local execution to remote
  execution; and
- remote backend support requires the future roadmap item 6.1 privacy and
  credentials work.

Update `docs/users-guide.md` to make the user-visible policy clear:

- v1 runs local analysis only;
- remote model execution is not available yet;
- remote model names or backends requested before a configured capability
  exists should fail clearly rather than silently call a service; and
- users should not expect profiles to store API keys.

Acceptance for this milestone:

- The technical design, developers' guide, and users' guide all point to the
  new ADR.
- The failure-mode text satisfies the roadmap success criterion.
- The user-facing text does not describe unimplemented commands or flags.

Run `coderabbit review --agent` after this milestone and clear concerns before
continuing.

### Milestone 3: Update roadmap and this plan

Update `docs/roadmap.md` item 1.1.3 from unchecked to checked only after the
ADR and signposts are complete. Add a decision bullet naming the new ADR and
summarizing the local-only policy.

Update this ExecPlan's living sections:

- mark completed progress items with implementation timestamps;
- record any ADR numbering changes in `Decision Log`;
- record CodeRabbit findings and their resolution in
  `Surprises & Discoveries`; and
- keep `Outcomes & Retrospective` current.

Acceptance for this milestone:

- Roadmap item 1.1.3 is marked done.
- The roadmap cites the new ADR as the durable decision record.
- This plan remains self-contained enough for another agent to continue.

### Milestone 4: Validate and commit

Run gates sequentially with logs under `/tmp`. Use this pattern, replacing the
action name for each gate:

```bash
make markdownlint 2>&1 | tee "/tmp/markdownlint-beatcue-$(git branch --show-current).out"
```

Required gates are:

```bash
make markdownlint
make nixie
make check-fmt
make lint
make typecheck
make test
```

The user explicitly requested `make check-fmt`, `make typecheck`, `make lint`,
and `make test`; this repository's Markdown guidance also requires
`make markdownlint` and `make nixie` for Markdown changes. If `make fmt` is
needed to fix Markdown wrapping or table formatting, run it before the final
`make check-fmt`.

If the gates pass, inspect the diff, stage the approved files, and commit with
the `commit-message` skill's file-based workflow. Do not use `git commit -m`.

Acceptance for this milestone:

- Each required gate passes.
- The commit contains only the approved 1.1.3 documentation changes.
- The commit message uses imperative mood and explains the local-only policy.

## Validation

During draft-plan creation, validate the plan itself with the same gates that
will be required for implementation:

```bash
make markdownlint 2>&1 | tee "/tmp/markdownlint-beatcue-$(git branch --show-current).out"
make nixie 2>&1 | tee "/tmp/nixie-beatcue-$(git branch --show-current).out"
make check-fmt 2>&1 | tee "/tmp/check-fmt-beatcue-$(git branch --show-current).out"
make typecheck 2>&1 | tee "/tmp/typecheck-beatcue-$(git branch --show-current).out"
make lint 2>&1 | tee "/tmp/lint-beatcue-$(git branch --show-current).out"
make test 2>&1 | tee "/tmp/test-beatcue-$(git branch --show-current).out"
```

Do not run these commands in parallel.

During implementation, the same gates must pass after the approved
documentation changes land. Because this task records a policy rather than
runtime code, no new pytest, pytest-bdd, syrupy, Hypothesis, CrossHair, or
Verus tests are expected in the documentation-only implementation. Later tasks
must add those tests when they implement runtime capability checks, CLI
behaviour, `agent-context` payloads, model-adapter ports, or credential
handling.

## Acceptance Criteria

This plan is ready for review when:

- `docs/execplans/1-1-3-record-local-only-policy-for-v1.md` exists and is
  self-contained.
- The plan says implementation requires explicit approval.
- The plan names the expected ADR, documentation signposts, quality gates,
  CodeRabbit checks, commit workflow, and draft pull request workflow.
- The branch is pushed as
  `1-1-3-record-local-only-policy-for-v1` with upstream tracking set to
  `origin/1-1-3-record-local-only-policy-for-v1`.
- A draft pull request exists with `(1.1.3)` in the title, a summary that
  mentions this ExecPlan, and a `## References` section linking the Lody
  session.

The future implementation is complete only when:

- the local-only and privacy policy ADR is accepted;
- the technical design, users' guide, developers' guide, and roadmap signpost
  the ADR;
- the roadmap item 1.1.3 is marked done;
- remote model execution remains out of scope until a later privacy and
  credentials design exists;
- the future failure contract for unsupported requested remote backends is
  clear;
- `coderabbit review --agent` concerns are cleared; and
- all required gates pass.

## Outcomes & Retrospective

The draft plan captures roadmap item 1.1.3 as a documentation and decision
ratification task with an explicit approval gate. CodeRabbit found one trivial
wording issue on the first pass and zero findings on the rerun. The first
validation pass succeeded for `make markdownlint`, `make nixie`,
`make check-fmt`, `make typecheck`, `make lint`, and `make test`.

The approved implementation added ADR 006, signposted it from the technical
design, users' guide, developers' guide, and roadmap, and marked roadmap item
1.1.3 done. Both implementation CodeRabbit reviews completed with zero
findings. Final validation passed for `make markdownlint`, `make nixie`,
`make check-fmt`, `make lint`, `make typecheck`, and `make test`. The final
complete-branch CodeRabbit review raised one trivial Markdown-validation
process concern that was addressed by inspecting ADR 006 and rerunning
`make markdownlint` successfully. The clean CodeRabbit rerun completed with
zero findings. The implementation is ready for the required commit and push.
