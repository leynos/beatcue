# Record the v1 schema decision for BeatCue JSON

This ExecPlan (execution plan) is a living document. The sections
`Constraints`, `Tolerances`, `Risks`, `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work
proceeds.

Status: COMPLETE

Implementation began after explicit approval in the user request dated
2026-05-10.

## Purpose / big picture

BeatCue needs a durable v1 schema decision before later domain, writer, CLI,
and snapshot work can converge on one output contract. The technical design
already states that BeatCue JSON uses `msgspec.Struct`, but roadmap item 1.1.1
is still open and asks for explicit ratification in an architectural decision
record (ADR) or equivalent design signpost.

After this plan is approved and implemented, a reviewer should be able to open
the documentation and see that BeatCue JSON has one selected v1 schema
technology, why that technology fits library callers and CLI output, how it
supports round-trip validation, and how snapshot stability will be protected.
The observable result is documentation alignment, not production serialization
code. Later implementation task 2.2.1 will build the actual BeatCue JSON
serializer and validation layer from this decision.

## Constraints

- Do not implement production BeatCue JSON serialization, domain schema
  classes, CLI commands, adapters, or writer code in this task. This is a
  decision-record task for roadmap item 1.1.1.
- Do not mark roadmap item 1.1.1 as complete until the implementation work
  described here has been approved, applied, validated, committed, pushed, and
  represented in a draft pull request.
- Preserve the v1 design boundary in `docs/beatcue-technical-design.md`:
  deterministic cue extraction for single-scene or single-shot videos is v1;
  semantic annotation, object tracking, OTIO enrichment, remote model
  execution, GPU scheduling, and advanced tracking remain post-v1 unless a
  later approved design update changes that boundary.
- Preserve the hexagonal architecture rule from the
  `hexagonal-architecture` skill: domain code owns domain values and ports, and
  infrastructure types do not leak inward. The schema decision must describe a
  serialization layer that maps immutable domain values into typed `msgspec`
  structures rather than making adapters the source of truth.
- Follow `docs/documentation-style-guide.md`: British English with Oxford
  spelling, sentence-case headings, wrapped prose, fenced code blocks with
  language identifiers, ADR naming as `docs/adr-NNN-short-description.md`, and
  required ADR sections.
- Keep the plan and all implementation edits self-contained. A future agent
  must be able to resume from this file without relying on chat history.
- Use the repository Makefile targets, not direct tool invocations, for quality
  gates. Run gates sequentially and log long outputs under `/tmp`.
- Do not run tests, linters, formatting, or format checks in parallel.
- Use Vidai Mock only if the approved implementation unexpectedly introduces
  behavioural tests for inference services. This roadmap item should not add
  inference-service code or tests, so Vidai Mock is expected to remain a
  signposted future testing tool, not an active dependency.

## Tolerances (exception triggers)

- Scope: if implementation requires modifying more than five files besides
  this ExecPlan, stop and ask whether the task should widen beyond schema
  ratification.
- Size: if the net documentation change exceeds 700 lines outside this
  ExecPlan, stop and ask whether to split the work.
- Dependency: if ratifying `msgspec.Struct` requires adding or changing Python
  dependencies now, stop and ask whether the task should include package wiring
  or remain documentation-only.
- Interface: if the plan cannot preserve the existing distinction between
  immutable domain values and serialization-specific `msgspec` structures, stop
  and present design options.
- ADR numbering: if another `docs/adr-003-*.md` appears before implementation,
  use the next available ADR number and record the change in `Decision Log`.
- Validation: if any required gate fails after two focused fix attempts, stop,
  record the failing command and log path, and ask for direction.
- Ambiguity: if multiple valid documentation forms would materially change the
  outcome, such as ADR-only versus technical-design-only ratification, stop and
  present the trade-offs. The default approved path in this plan is to add an
  ADR because the roadmap explicitly mentions a separate decision record.

## Risks

- Risk: The technical design already states `msgspec.Struct` as the selected
  v1 schema technology, so adding an ADR may duplicate text. Severity: low
  Likelihood: medium Mitigation: make the ADR the durable decision record and
  keep the technical design as a concise signpost to that ADR, rather than
  repeating every option and trade-off in both places.

- Risk: Ratifying `msgspec.Struct` before serializer implementation may hide a
  later incompatibility with snapshots, Python 3.14, or the public writer API.
  Severity: medium Likelihood: medium Mitigation: record the rationale,
  non-goals, validation expectations, and escape hatch: replacing `msgspec`
  requires a new ADR or design update before implementation continues.

- Risk: Documentation could imply that BeatCue JSON is already implemented.
  Severity: medium Likelihood: low Mitigation: phrase user and developer guide
  changes as planned contracts unless the implementation already exists. The
  current repository only has a package smoke check and planned API/CLI
  documentation.

- Risk: The roadmap may be marked done too early.
  Severity: medium Likelihood: low Mitigation: update `docs/roadmap.md` only
  after the ADR and signposts are in place and validation has passed. The
  roadmap entry should become `[x]` in the same approved implementation commit.

- Risk: Full Python gates may perform environment writes even though the
  implementation is documentation-only. Severity: low Likelihood: medium
  Mitigation: still run the user-requested gates after documentation gates:
  `make check-fmt`, `make typecheck`, `make lint`, and `make test`, using tee
  logs. If an environmental permission failure occurs, request elevated sandbox
  permissions rather than bypassing the gate.

## Progress

- [x] (2026-05-10 00:00Z) Loaded the `execplans`,
  `hexagonal-architecture`, `leta`, and `vidai-mock` skills relevant to this
  planning task.
- [x] (2026-05-10 00:00Z) Checked the current branch and confirmed it was not
  the main branch.
- [x] (2026-05-10 00:00Z) Added this repository to the Leta workspace.
- [x] (2026-05-10 00:00Z) Used a Wyvern agent to review the roadmap, technical
  design, ADR conventions, and likely validation path for roadmap item 1.1.1.
- [x] (2026-05-10 00:00Z) Renamed the local branch to
  `1-1-1-record-v1-schema-decision-for-beat-cue-json`.
- [x] (2026-05-10 00:00Z) Drafted this ExecPlan at
  `docs/execplans/1-1-1-record-v1-schema-decision-for-beat-cue-json.md`.
- [x] (2026-05-10 00:00Z) Validated the draft plan with `make markdownlint`,
  `make nixie`, `make check-fmt`, `make typecheck`, `make lint`, and
  `make test`.
- [x] (2026-05-10 00:00Z) Received explicit approval to implement this
  ExecPlan.
- [x] (2026-05-10 00:00Z) Used Firecrawl to check current `msgspec` prior art
  and confirmed that its public documentation still describes typed schemas,
  JSON encoding and decoding, validation during decoding, performance, and no
  required dependencies.
- [x] (2026-05-10 00:00Z) Created
  `docs/adr-007-v1-beatcue-json-schema.md` to ratify `msgspec.Struct` for the
  BeatCue JSON v1 serialization boundary.
- [x] (2026-05-10 00:00Z) Added design, user-guide, and developer-guide
  signposts so public and internal documentation point at ADR 007 without
  claiming the serializer exists.
- [x] (2026-05-10 00:00Z) Marked roadmap item 1.1.1 done and linked the item
  to ADR 007.
- [x] (2026-05-10 00:00Z) Ran Markdown gates and the user-requested Python
  gates sequentially with tee logs under `/tmp`. `make markdownlint`,
  `make nixie`, `make check-fmt`, `make typecheck`, `make lint`, and
  `make test` passed.
- [x] (2026-05-10 00:00Z) Committed the approved documentation changes as
  `42364399e96249c24b9b9bb1f4ba452a4cdbf182`.
- [x] (2026-05-10 00:00Z) Pushed the branch tracking
  `origin/1-1-1-record-v1-schema-decision-for-beat-cue-json`.
- [x] (2026-05-10 00:00Z) Updated draft pull request
  <https://github.com/leynos/beatcue/pull/7> with a `(1.1.1)` title and a
  summary that mentions this ExecPlan.

## Surprises & discoveries

- Observation: `docs/beatcue-technical-design.md` §13.1 already says BeatCue
  JSON uses `msgspec.Struct` definitions as the v1 schema technology. Evidence:
  the section describes immutable domain values mapped to typed `msgspec`
  structures for JSON encoding, decoding, and validation. Impact:
  implementation should ratify and signpost the existing design decision rather
  than re-litigating schema technology from scratch.

- Observation: `docs/roadmap.md` still has item 1.1.1 unchecked even though
  the technical design contains the selected technology. Evidence: roadmap item
  1.1.1 asks to record the v1 schema decision and explains that success
  requires rationale for library callers, CLI output, round-trip validation,
  and stable snapshots. Impact: the implementation should close this
  consistency gap with an ADR and roadmap update.

- Observation: The repository already has ADR conventions and two accepted
  ADRs. Evidence: `docs/adr-001-colourgram-domain-boundary.md` and
  `docs/adr-002-v1-port-surface.md` are accepted ADRs dated 2026-05-09. Impact:
  the new ADR should probably be `docs/adr-007-v1-beatcue-json-schema.md`
  unless another ADR is added first.

- Observation: The repository Makefile defines Markdown gates separately from
  Python gates, but the user explicitly requested `make check-fmt`,
  `make typecheck`, `make lint`, and `make test`. Evidence: `AGENTS.md` says
  Markdown-only changes require `make markdownlint` and `make nixie`; the user
  request adds the Python gates. Impact: the implementation should run both the
  Markdown gates and the user-requested Python gates.

- Observation: Firecrawl found the current `msgspec` public documentation and
  scraped <https://jcristharif.com/msgspec/>. Evidence: that documentation
  describes `msgspec` as a fast serialization and validation library with JSON
  support, type-annotation-based schema validation, a `Struct` type for
  structured data, JSON encode/decode examples, and no required dependencies.
  Impact: the ADR can cite external prior art for the existing design choice,
  while keeping BeatCue's decision grounded in local architecture boundaries
  and writer-contract needs.

- Observation: `make fmt` still fails in its broad Markdown formatter path
  after reporting line-length and table-alignment issues in existing
  repository documents outside this task. Evidence: the log is
  `/tmp/fmt-1-1-1-record-v1-schema-decision-for-beat-cue-json.out`. Impact:
  unrelated formatter churn was restored, and the narrower required gates were
  run successfully. This matches the same known behaviour observed during the
  plan-only change.

- Observation: `make typecheck` generated an untracked `uv.lock` while syncing
  the development environment. Evidence: `git status --short` showed
  `?? uv.lock` after the gate. Impact: the generated lock file was removed
  because this documentation-only task does not change dependencies.

## Decision log

- Decision: Draft this plan as approval-gated and do not implement the
  decision record until the user explicitly approves it. Rationale: the
  `execplans` skill requires a draft phase followed by explicit approval before
  execution, and the user stated that the plan must be approved before it is
  implemented. Date/Author: 2026-05-10 / Codex.

- Decision: Plan to create an ADR rather than relying only on the existing
  technical design paragraph. Rationale: `docs/roadmap.md` item 1.1.1
  explicitly asks to ratify `msgspec.Struct` in an ADR if the project still
  wants a separate decision record. The repository already uses ADRs for
  phase-1 boundary decisions, and this schema decision gates later writer and
  snapshot work. Date/Author: 2026-05-10 / Codex.

- Decision: Treat production serializer tests as out of scope for item 1.1.1.
  Rationale: the roadmap separates schema ratification from item 2.2.1, which
  implements BeatCue JSON serialization and validation. This plan should
  specify future unit, property, behavioural, and snapshot expectations without
  adding implementation tests before the production surface exists.
  Date/Author: 2026-05-10 / Codex.

- Decision: Signpost Vidai Mock but do not start it for this work.
  Rationale: the user requested Vidai Mock for behavioural testing of inference
  services, but this task does not implement inference-service behaviour.
  Starting or depending on Vidai Mock here would widen the task beyond schema
  ratification. Date/Author: 2026-05-10 / Codex.

- Decision: Use `docs/adr-007-v1-beatcue-json-schema.md` as the ADR file.
  Rationale: no newer ADR number appeared before implementation, and the
  existing repository sequence ends at ADR 002. Date/Author: 2026-05-10 / Codex.

- Decision: Do not add pytest, pytest-bdd, syrupy, or Hypothesis tests in this
  task. Rationale: the implementation is an ADR and documentation signpost
  change only; there is no executable serializer, CLI workflow, or public
  output contract to test yet. ADR 007 records those test obligations for the
  later BeatCue JSON writer implementation. Date/Author: 2026-05-10 / Codex.

## Outcomes & retrospective

Implemented the schema ratification as documentation-only work. The change
adds `docs/adr-007-v1-beatcue-json-schema.md`, signposts ADR 007 from
`docs/beatcue-technical-design.md`, `docs/users-guide.md`, and
`docs/developers-guide.md`, and marks roadmap item 1.1.1 done in
`docs/roadmap.md`.

The implementation commit is
`42364399e96249c24b9b9bb1f4ba452a4cdbf182`. The draft pull request is
<https://github.com/leynos/beatcue/pull/7>.

Validation evidence:

- `make fmt 2>&1 | tee /tmp/fmt-1-1-1-record-v1-schema-decision-for-beat-cue-json.out`
  was attempted and failed in the repository's broad Markdown formatter path
  on existing long table and line-length issues outside this task. Formatter
  churn in unrelated files was restored.
- `make markdownlint 2>&1 | tee /tmp/markdownlint-1-1-1-record-v1-schema-decision-for-beat-cue-json.out`
  passed.
- `make nixie 2>&1 | tee /tmp/nixie-1-1-1-record-v1-schema-decision-for-beat-cue-json.out`
  passed.
- `make check-fmt 2>&1 | tee /tmp/check-fmt-1-1-1-record-v1-schema-decision-for-beat-cue-json.out`
  passed.
- `make typecheck 2>&1 | tee /tmp/typecheck-1-1-1-record-v1-schema-decision-for-beat-cue-json.out`
  passed.
- `make lint 2>&1 | tee /tmp/lint-1-1-1-record-v1-schema-decision-for-beat-cue-json.out`
  passed.
- `make test 2>&1 | tee /tmp/test-1-1-1-record-v1-schema-decision-for-beat-cue-json.out`
  passed.

No production serializer, package dependency, CLI command, inference-service
behaviour, or test suite was added. ADR 007 records the required pytest,
pytest-bdd, syrupy, Hypothesis, and Vidai Mock expectations for the later
writer and inference-service implementation tasks.

## Context and orientation

The relevant repository files are:

- `docs/roadmap.md`: the delivery roadmap. Item 1.1.1 asks to record the v1
  schema decision for BeatCue JSON and defines success as explaining why
  `msgspec` is suitable for library callers, CLI output, round-trip validation,
  and stable snapshots.
- `docs/beatcue-technical-design.md`: the primary technical design. Section 7
  defines the domain model and `AnalysisResult`; section 13.1 defines BeatCue
  JSON and already names `msgspec.Struct`; section 17 defines testing and
  verification expectations; section 21 lists deferred decisions and no longer
  treats schema technology as deferred.
- `docs/documentation-style-guide.md`: the documentation and ADR style guide.
  It defines ADR naming, required sections, optional sections, British English
  with Oxford spelling, Markdown wrapping, and table captions.
- `docs/users-guide.md`: user-facing planned library and CLI contracts. It
  must not claim BeatCue JSON serialization is implemented until later code
  lands.
- `docs/developers-guide.md`: contributor-facing architecture, writer, and
  testing guidance. It should point implementers at the ADR if it discusses
  BeatCue JSON schema work.
- `docs/adr-001-colourgram-domain-boundary.md` and
  `docs/adr-002-v1-port-surface.md`: existing ADR examples and numbering
  precedent.

Terms used in this plan:

- BeatCue JSON: the planned lossless JSON output for an `AnalysisResult`,
  containing media metadata, feature summaries, cues, diagnostics,
  configuration, and provenance.
- `AnalysisResult`: the canonical application return value defined in the
  technical design. All machine writers consume this value.
- `msgspec.Struct`: a typed Python structure from the `msgspec` library used
  to define fast serializable and validatable JSON shapes.
- Round-trip validation: decoding an encoded BeatCue JSON document back through
  the same schema and verifying that required values, cue IDs, ordering,
  diagnostics, and provenance survive unchanged.
- Stable snapshots: serialized output captured by snapshot tests so reviewers
  can see intentional contract changes.
- Hexagonal architecture: an architecture where dependencies point inward.
  Domain code owns domain values and ports; adapters implement ports and
  convert infrastructure types at the boundary.

Relevant skills and why they matter:

- `execplans`: governs this approval-gated plan and requires the living
  sections in this document.
- `hexagonal-architecture`: constrains the schema decision so serialization
  does not leak adapter or framework concerns into the domain model.
- `leta`: should be used for later code navigation when implementation tasks
  begin.
- `vidai-mock`: applies only if a future approved task introduces behavioural
  tests for inference services. It is not needed for this documentation-only
  schema decision.

## Implementation plan

### Milestone 1: Verify current documentation state

Read `docs/roadmap.md`, `docs/beatcue-technical-design.md`,
`docs/documentation-style-guide.md`, `docs/users-guide.md`,
`docs/developers-guide.md`, and the existing ADR files. Confirm that the
technical design still selects `msgspec.Struct` and that no newer ADR number
has appeared.

Acceptance for this milestone:

- The next ADR number is known.
- Any text that conflicts with the `msgspec.Struct` decision is listed in
  `Surprises & Discoveries`.
- If the current documentation has already been changed by another agent, this
  ExecPlan is updated before edits proceed.

### Milestone 2: Add the schema ADR

Create `docs/adr-007-v1-beatcue-json-schema.md`, or the next available ADR
number if `003` is taken. Use the documentation style guide's ADR structure.
The ADR should be `Accepted` and dated with the implementation date.

The ADR must cover:

- context: BeatCue JSON is the lossless `AnalysisResult` interchange format
  and later writer work needs a stable schema decision;
- decision drivers: library callers, CLI output, round-trip validation,
  snapshot stability, Python typing, hexagonal boundaries, and bounded output;
- options considered: `msgspec.Struct`, dataclasses plus ad hoc JSON,
  Pydantic-style models, and JSON Schema-first generation;
- decision outcome: v1 uses `msgspec.Struct` in a serialization layer while
  preserving immutable domain values;
- goals and non-goals: ratify schema technology without implementing the
  serializer, changing domain APIs, or adding inference-service behaviour;
- known risks and limitations: migration if `msgspec` proves unsuitable,
  schema-version discipline, and avoiding framework leakage into domain code;
- testing expectations for later implementation: pytest unit tests for schema
  mapping, Hypothesis tests for invariants, syrupy snapshots for output
  stability, pytest-bdd for externally observable CLI or library workflows once
  they exist, and Vidai Mock only for later inference-service behaviours.

Acceptance for this milestone:

- The ADR explains why `msgspec` is suitable for library callers, CLI output,
  round-trip validation, and stable snapshots.
- The ADR explicitly distinguishes domain values from serialization-specific
  schema structures.
- The ADR does not claim that BeatCue JSON serialization is already
  implemented.

### Milestone 3: Add design and guide signposts

Update `docs/beatcue-technical-design.md` §13.1 so it points to the new ADR as
the durable record for the `msgspec.Struct` choice. Keep the existing design
concise and avoid duplicating the full ADR.

Review `docs/users-guide.md` and `docs/developers-guide.md`. Update only the
small passages needed to keep consumer and implementer expectations aligned.
Likely updates are:

- the users' guide says BeatCue JSON is planned v1 output and points to the
  selected schema technology only as a contract for future implementation;
- the developers' guide writer section points implementers to the ADR for the
  `msgspec.Struct` decision and reminds them that schema structs belong at the
  serialization boundary.

Acceptance for this milestone:

- The design document and guides agree that `msgspec.Struct` is the selected
  v1 schema technology.
- No user-facing text implies unavailable commands or serializers already
  exist.
- No internal-facing text encourages imports from adapters into domain code.

### Milestone 4: Close roadmap item 1.1.1

Update `docs/roadmap.md` to mark item 1.1.1 as done after the ADR and signposts
are complete. Add a concise reference to the ADR under the item so future
readers can follow the decision record.

Acceptance for this milestone:

- The roadmap checkbox for `1.1.1` is `[x]`.
- The item cites the ADR or design signpost that ratifies `msgspec.Struct`.
- The change does not mark dependent tasks as complete.

### Milestone 5: Validate, commit, push, and open the draft PR

Run gates sequentially from the repository root and capture logs under `/tmp`.
Use filenames that include the branch name, for example:

```bash
make fmt 2>&1 | tee /tmp/fmt-1-1-1-record-v1-schema-decision-for-beat-cue-json.out
make markdownlint 2>&1 | tee /tmp/markdownlint-1-1-1-record-v1-schema-decision-for-beat-cue-json.out
make nixie 2>&1 | tee /tmp/nixie-1-1-1-record-v1-schema-decision-for-beat-cue-json.out
make check-fmt 2>&1 | tee /tmp/check-fmt-1-1-1-record-v1-schema-decision-for-beat-cue-json.out
make typecheck 2>&1 | tee /tmp/typecheck-1-1-1-record-v1-schema-decision-for-beat-cue-json.out
make lint 2>&1 | tee /tmp/lint-1-1-1-record-v1-schema-decision-for-beat-cue-json.out
make test 2>&1 | tee /tmp/test-1-1-1-record-v1-schema-decision-for-beat-cue-json.out
```

If `make fmt` changes files, inspect those changes before continuing. If any
gate fails for an environmental permission reason, rerun it with elevated
sandbox permissions. If a gate fails for a real documentation or code issue,
fix it within the tolerances and rerun the failed gate.

After validation passes:

1. Commit the documentation changes with a concise imperative subject and a
   body explaining the ADR, signposts, and roadmap closure.
2. Push the branch with upstream tracking:
   `git push -u origin 1-1-1-record-v1-schema-decision-for-beat-cue-json`.
3. Open a draft pull request. The title must include `(1.1.1)`, and the
   summary must mention this ExecPlan:
   `docs/execplans/1-1-1-record-v1-schema-decision-for-beat-cue-json.md`.

Acceptance for this milestone:

- All required gates pass.
- The commit exists on the renamed branch.
- The remote branch tracks
  `origin/1-1-1-record-v1-schema-decision-for-beat-cue-json`.
- A draft pull request exists with the required title and ExecPlan reference.

## Validation strategy

This task is documentation ratification. It does not introduce production
schema code, so new pytest, pytest-bdd, syrupy, or Hypothesis tests are not
expected in this task. The plan records those testing requirements in the ADR
for the later implementation task that creates the serializer and externally
observable output.

For this task, validation consists of:

- `make fmt` to format Markdown and source files;
- `make markdownlint` for Markdown style;
- `make nixie` for Mermaid validation;
- `make check-fmt` because the user explicitly requested it;
- `make typecheck` because the user explicitly requested it;
- `make lint` because the user explicitly requested it;
- `make test` because the user explicitly requested it.

Expected result for each command is exit code `0`. Keep the `/tmp` log paths in
the final implementation summary and in this plan's retrospective.

## Approval gate

This document is a plan only. Do not begin the implementation milestones above
until the user explicitly approves this ExecPlan or requests specific
revisions. Once approved, implement within the tolerances, update this plan as
the work proceeds, and stop for direction if an exception trigger is reached.
