# Record the v1 object-tracking boundary

This ExecPlan (execution plan) is a living document. The sections `Constraints`,
`Tolerances`, `Risks`, `Progress`, `Surprises & Discoveries`, `Decision log`,
and `Outcomes & Retrospective` must be kept up to date as work proceeds.

Status: COMPLETE

This plan was explicitly approved for implementation on 2026-05-17. Approval
means implementing the documentation and decision-record changes described
here; it does not approve object-tracking production code.

## Purpose / big picture

Roadmap item 1.1.2 closes the remaining object-tracking deferral in the phase 1
architecture ratification work. BeatCue v1 currently excludes object tracking
from the first deterministic product, but later object-entry and object-exit
tasks still need one selected boundary so they do not reopen the model-adapter
decision.

After this plan is approved and implemented, a reviewer should be able to open
the documentation and see which v1/post-v1 boundary BeatCue has selected:
Florence-2 detections only, a centroid tracker, or a domain-owned pluggable
tracker port with a simple default. The observable outcome is documentation
alignment: an architectural decision record (ADR), updated design signposts,
developer and user guidance, and a roadmap update. Later implementation task
5.2.1 will build the selected object tracker adapter from this decision.

## Constraints

- Do not implement production object tracking, object-entry cue extraction,
  Florence-2 inference, centroid-association code, command-line interface (CLI)
  commands, adapters, or writer changes in this task. This task records the
  boundary decision.
- Do not overwrite
  `docs/execplans/1-1-1-record-v1-schema-decision-for-beat-cue-json.md`. That
  file is the completed plan for roadmap item 1.1.1 and is part of project
  history.
- Treat `docs/roadmap.md` as the source of truth for task identity. The task
  text in this request describes roadmap item 1.1.2, even though the requested
  filename named the already completed 1.1.1 plan.
- Preserve the v1 product boundary in
  `docs/beatcue-technical-design.md` section 3.1: deterministic cue extraction
  for single-scene or single-shot videos is v1, while semantic annotation and
  object tracking remain post-v1 unless an approved ADR changes that boundary.
- Preserve the hexagonal architecture rule from the
  `hexagonal-architecture` skill: the domain owns ports and object-tracking
  concepts, while Florence-2, OpenCV, or other infrastructure-specific types
  stay in adapters.
- Use `docs/adr-008-v1-object-tracking-boundary.md` for the decision record.
  ADR 004 now belongs to the two-tier Python linting decision on `origin/main`;
  the object-tracking decision was renumbered during rebase to preserve both
  branches' ADRs.
- Follow `docs/documentation-style-guide.md`: British English with Oxford
  spelling, sentence-case headings, wrapped prose, fenced code blocks with
  language identifiers, ADR naming conventions, captions for tables, and
  required ADR sections.
- Signpost the relevant skills in the implementation notes:
  `execplans`, `hexagonal-architecture`, `leta`, `firecrawl-mcp`, and
  `commit-message`. Use `vidai-mock` only if implementation unexpectedly
  introduces behavioural tests for an inference service.
- Use Makefile targets for quality gates. Run gates sequentially and write
  logs under `/tmp`; do not run tests, linters, formatting, or format checks in
  parallel.
- Use `coderabbit review --agent` after each major implementation milestone,
  record concerns in this plan, and clear all concerns before moving on.
- Commit each approved implementation milestone only after its required gates
  pass.

## Tolerances (exception triggers)

- Scope: if implementation requires modifying more than six files besides this
  ExecPlan, stop and ask whether the task should widen beyond decision
  ratification.
- Size: if the net documentation change exceeds 900 lines outside this
  ExecPlan, stop and ask whether to split the work.
- Dependencies: if the decision requires adding or changing Python
  dependencies now, stop and ask whether package wiring should move into a
  separate roadmap item.
- Interface: if implementation would change public Python APIs, CLI behaviour,
  persisted output formats, or BeatCue JSON fields, stop and ask for approval.
- Boundary: if the selected decision would move object tracking into the v1
  deterministic release rather than leaving it post-v1 behind ports, stop and
  present the release-scope trade-off.
- ADR numbering: if another `docs/adr-004-*.md` appears before implementation,
  use the next available ADR number and record the change in `Decision log`.
- Validation: if any required gate fails after two focused fix attempts, stop,
  record the failing command and log path, and ask for direction.
- Review: if `coderabbit review --agent` raises concerns that require
  implementation beyond the tolerances above, stop and ask for direction.
- Ambiguity: if multiple valid documentation forms materially change the
  outcome, such as ADR-only versus design-document-only ratification, stop and
  present the trade-offs. The default path is an ADR plus concise signposts.

## Risks

- Risk: The request named the completed 1.1.1 ExecPlan path while the pasted
  roadmap task is 1.1.2. Severity: medium. Likelihood: high. Mitigation: keep
  the completed 1.1.1 plan intact, draft this corrected 1.1.2 plan, and record
  the mismatch in `Decision log`.

- Risk: The object-tracking decision could accidentally expand v1 beyond the
  deterministic product boundary. Severity: high. Likelihood: medium.
  Mitigation: make the ADR explicit that object tracking remains post-v1 for
  implementation, while v1 establishes the port boundary and deferred decision.

- Risk: Florence-2 can provide object detections, but detections alone do not
  prove persistence across frames. Severity: high. Likelihood: high.
  Mitigation: choose a boundary that separates detection observations from
  track persistence, and require later object-entry tasks to test
  `min_track_persistence_s` before emitting entry or exit cues.

- Risk: A centroid tracker may be too weak for occlusion, re-identification,
  and camera-motion-heavy scenes. Severity: medium. Likelihood: medium.
  Mitigation: document it as a simple default behind a pluggable port rather
  than the permanent tracking strategy.

- Risk: OpenCV includes tracking APIs, which could tempt adapters to leak
  OpenCV state into the domain. Severity: medium. Likelihood: medium.
  Mitigation: the ADR must state that domain values carry plain observations,
  boxes, timestamps, track IDs, confidence, and diagnostics only.

- Risk: Documentation could imply object tracking is already implemented.
  Severity: medium. Likelihood: low. Mitigation: phrase user-guide changes as
  planned or deferred behaviour unless implementation already exists.

## Progress

- [x] (2026-05-13 22:49Z) Loaded the `leta`, `execplans`,
  `hexagonal-architecture`, `firecrawl-mcp`, and `commit-message` skills
  relevant to this planning task.
- [x] (2026-05-13 22:49Z) Checked the current branch and confirmed it is
  `1-1-2-record-v1-object-tracking-boundary`, not the main branch.
- [x] (2026-05-13 22:49Z) Added this repository to the Leta workspace and
  confirmed that the codebase currently contains only the small package smoke
  skeleton.
- [x] (2026-05-13 22:49Z) Used a Wyvern agent to review the roadmap, existing
  schema decision plan, and technical-design sections relevant to 1.1.1 and
  1.1.2.
- [x] (2026-05-13 22:49Z) Used Firecrawl to review current Florence-2,
  Hugging Face object-detection, and OpenCV tracking documentation as prior art
  for the boundary decision.
- [x] (2026-05-13 22:49Z) Drafted this corrected ExecPlan at
  `docs/execplans/1-1-2-record-v1-object-tracking-boundary.md`.
- [x] (2026-05-13 22:49Z) Ran `coderabbit review --agent` on the draft. The
  first run reported four minor documentation-style findings; the findings were
  fixed, and the rerun completed with zero findings.
- [x] (2026-05-13 22:49Z) Validated the draft plan with `make markdownlint`,
  `make nixie`, `make check-fmt`, `make typecheck`, `make lint`, and
  `make test`.
- [x] (2026-05-16 20:30Z) Addressed review feedback by updating stale branch
  context, normalizing centroid-association terminology, expanding first-use
  acronyms, and replacing duplicated gate and test detail with references to
  the developers' guide.
- [x] (2026-05-17 11:35Z) Received explicit approval to implement the
  decision-record changes from this ExecPlan.
- [x] (2026-05-17 11:35Z) Confirmed ADR 008 is available and the working tree
  starts clean against `origin/1-1-2-record-v1-object-tracking-boundary`.
- [x] (2026-05-17 11:35Z) Updated this plan to `IN PROGRESS` before editing
  design documents.
- [x] (2026-05-17 11:35Z) Created ADR 008 and added documentation signposts in
  the technical design, developers' guide, users' guide, and roadmap.
- [x] Create the ADR and documentation signposts.
- [x] (2026-05-17 11:48Z) Ran `coderabbit review --agent`. The first
  implementation review found two valid minor ADR issues, which were fixed. The
  second review emitted stale line-wrap findings after the file had already
  been rechecked locally; a third review completed with zero findings.
- [x] Run `coderabbit review --agent` and clear concerns.
- [x] (2026-05-17 11:50Z) Ran `make markdownlint`, `make nixie`,
  `make check-fmt`, `make lint`, `make typecheck`, and `make test` sequentially
  with `/tmp` logs. All gates passed.
- [x] Run documentation gates and the user-requested Python gates.
- [x] (2026-05-17 11:54Z) Committed the approved implementation changes as
  `d52976f` (`Record object-tracking boundary`) after rebasing onto
  `origin/main`.
- [x] Commit the approved implementation changes.
- [x] (2026-05-17 12:05Z) Rebasing onto `origin/main` found that main had
  introduced `docs/adr-004-two-tier-python-linting.md` and architecture checker
  guidance. Resolved the conflict by keeping main's architecture guidance,
  preserving this branch's object-tracking boundary text, and renumbering the
  object-tracking decision to ADR 008.

## Surprises & discoveries

- Observation: `docs/roadmap.md` already marks roadmap item 1.1.1 complete and
  links the decision to ADR 007. Impact: this work must not reopen the BeatCue
  JSON schema decision.

- Observation:
  `docs/execplans/1-1-1-record-v1-schema-decision-for-beat-cue-json.md` already
  exists and has `Status: COMPLETE`. Impact: overwriting that file would
  destroy completed plan history and contradict the roadmap.

- Observation: The pasted roadmap text in the request is exactly item 1.1.2,
  "Record the v1 object-tracking boundary". Impact: this plan uses a corrected
  1.1.2 filename and records the mismatch for user review.

- Observation: `docs/beatcue-technical-design.md` section 3.1 currently places
  object tracking in post-v1 work, while section 21 says the first object
  tracker is deferred. Impact: the implementation should close the deferral
  without forcing object tracking into the first deterministic release.

- Observation: Firecrawl found the current Hugging Face Florence-2 model card,
  which describes Florence-2 as a prompt-based vision foundation model that can
  perform object detection and return bounding boxes and labels for an `<OD>`
  prompt. Impact: Florence-2 is viable as a detection adapter, but it is not by
  itself a persistence boundary.

- Observation: Firecrawl found the current Hugging Face object-detection task
  documentation, which defines object detection as image input producing
  bounding boxes and associated labels. Impact: the ADR should distinguish
  per-frame detections from cross-frame tracks.

- Observation: Firecrawl found the OpenCV tracking API documentation, which
  includes `Tracker`, `MultiTracker`, trajectories, confidence maps, and
  several tracker implementations. Impact: there is prior art for pluggable
  tracking implementations, but BeatCue should hide those details behind a
  domain-owned port.

- Observation: The first `coderabbit review --agent` run found only
  documentation-style issues in this draft: sentence-case heading text and
  80-column wrapping. Impact: the draft was rewrapped, the heading was changed
  to `Decision log`, and the rerun completed with zero findings.

- Observation: The first implementation `coderabbit review --agent` run found
  two minor ADR 008 documentation issues: the title used `V1` instead of `v1`,
  and the first `SAM 2` mention was not expanded. Impact: both findings were
  valid and fixed before validation gates.

- Observation: Rebasing onto `origin/main` showed that main had already added
  `docs/adr-004-two-tier-python-linting.md`. Impact: the object-tracking ADR
  was renamed to ADR 008, so both decisions remain addressable.

## Decision log

- Decision: Draft a new plan for roadmap item 1.1.2 instead of overwriting the
  requested 1.1.1 path. Rationale: `docs/roadmap.md` marks 1.1.1 complete, the
  requested path already contains a completed ExecPlan, and the pasted task
  text describes 1.1.2. Date/Author: 2026-05-13 / Codex.

- Decision: Recommend an ADR for the object-tracking boundary rather than only
  editing the technical design. Rationale: roadmap phase 1.1 is about ratifying
  architecture and deferred decisions, existing phase-1 decisions already use
  ADRs, and task 5.2.1 explicitly depends on the selected boundary.
  Date/Author: 2026-05-13 / Codex.

- Decision: Treat production tracking tests as out of scope for item 1.1.2.
  Rationale: the roadmap separates boundary ratification from task 5.2.1, which
  implements the object tracker adapter. This plan still records the later
  unit, property, behavioural, snapshot, and Vidai Mock obligations for
  implementation tasks that introduce executable tracking or inference
  behaviour. Date/Author: 2026-05-13 / Codex.

- Decision: The default proposed ADR outcome is "pluggable object tracker port
  with a simple centroid-association default, fed by detector observations such
  as Florence-2". Rationale: this preserves the hexagonal boundary, keeps
  Florence-2 as a detector rather than a tracker, gives later object-entry
  tasks a simple implementable default, and leaves room for OpenCV, SAM 2, or
  other future tracking adapters. Date/Author: 2026-05-13 / Codex.

## Implementation plan

Implementation must begin only after explicit user approval. On approval, first
change `Status: DRAFT` to `Status: IN PROGRESS` and add a progress entry with
the approval timestamp.

The implementation should start by checking the working tree and ADR sequence:

```bash
git status --short
find docs -maxdepth 1 -type f -name 'adr-*.md' | sort
```

Because `origin/main` now owns ADR 004, the implementation uses
`docs/adr-008-v1-object-tracking-boundary.md`. If ADR 008 already exists in a
future replay, use the next available number and update this plan. The ADR
should include the sections required by `docs/documentation-style-guide.md` and
should compare these options:

- Florence-2-only detections with no persistence boundary.
- A centroid tracker as the selected object-tracking implementation.
- A pluggable domain-owned `ObjectTracker` port with a simple
  centroid-association default and detector adapters feeding plain observations.

The ADR should accept the pluggable port with a simple centroid-association
default unless new evidence changes the trade-off. It should state that
Florence-2 is a useful detection and labelling adapter, not the persistence
boundary. It should also state that the domain-owned port exchanges plain data:
frame timestamp, source frame identity, bounding box coordinates, optional
label, confidence, stable track ID, track lifecycle, and diagnostics. It must
not expose OpenCV, Transformers, Torch, PIL, or adapter-specific objects in
domain signatures.

Update `docs/beatcue-technical-design.md` in the sections already cited by the
roadmap:

- Section 3.1 should continue to say object tracking is post-v1
  implementation work, while noting that ADR 008 records the selected boundary
  for later tasks.
- Section 8 should describe `ObjectTracker` as a domain-owned port whose
  default implementation may be centroid-association over detector observations.
- Section 11 should keep the persistence requirement for object-entry and
  object-exit cues and point to the ADR for the selected boundary.
- Section 12 should preserve the rule that semantic annotation describes
  visible evidence only and does not replace tracking persistence.
- Section 21 should replace the open deferral with a concise signpost to
  [ADR 008](../adr-008-v1-object-tracking-boundary.md), while leaving remote
  models, graphics processing unit (GPU) scheduling, and advanced segmentation
  deferred.

Update `docs/developers-guide.md` with internal guidance for later
implementers: keep tracker protocols in the domain, keep detector and tracker
adapters outside the domain, use deterministic fixtures for centroid
association, use property tests for track lifecycle invariants, and use Vidai
Mock only for behavioural tests that exercise inference-service adapters.

Update `docs/users-guide.md` only if needed to avoid stale public wording. The
user guide should not promise object tracking in the current usable product. If
it mentions planned object tracking, it should say that tracking is deferred
post-v1 and that the architecture now has a selected boundary for later work.

Update `docs/roadmap.md` only after the ADR and signposts are in place. Mark
roadmap item 1.1.2 done and add a decision line pointing to the ADR. Do not
mark task 5.2.1 done.

After the first documentation pass, run CodeRabbit and the repository quality
gates sequentially, using the `tee` log workflow described in
`docs/developers-guide.md` and the root `AGENTS.md`. If CodeRabbit reports
concerns, record them in `Surprises & discoveries` or `Decision log`, fix them
within the tolerances, and rerun the review. If the command is unavailable or
cannot determine a pull request for this branch, record the exact failure and
continue only if the failure is environmental rather than a review concern.

If documentation-only work does not add executable tests, record that decision
in this plan. Later object-tracker implementation work must follow the testing
strategy in `docs/developers-guide.md`, including property-based, behavioural,
snapshot, and inference-adapter coverage where those boundaries are touched.

Commit the approved implementation with the file-based commit-message workflow
from the `commit-message` skill:

```bash
git status --short
git diff -- \
  docs/adr-008-v1-object-tracking-boundary.md \
  docs/beatcue-technical-design.md \
  docs/developers-guide.md \
  docs/users-guide.md \
  docs/roadmap.md \
  docs/execplans/1-1-2-record-v1-object-tracking-boundary.md
git add \
  docs/adr-008-v1-object-tracking-boundary.md \
  docs/beatcue-technical-design.md \
  docs/developers-guide.md \
  docs/users-guide.md \
  docs/roadmap.md \
  docs/execplans/1-1-2-record-v1-object-tracking-boundary.md
COMMIT_MSG_DIR=$(mktemp -d)
$EDITOR "$COMMIT_MSG_DIR/COMMIT_MSG.md"
git commit -F "$COMMIT_MSG_DIR/COMMIT_MSG.md"
rm -rf "$COMMIT_MSG_DIR"
```

Use a summary such as `Record object-tracking boundary` and a body explaining
that the commit ratifies the deferred tracking boundary without implementing
tracking.

## Validation

For the plan draft itself, validation consists of Markdown formatting and the
full user-requested quality gates passing on the repository state. For the
approved implementation, validation consists of:

- `coderabbit review --agent` having no unresolved concerns, or a documented
  environmental failure if the command cannot run in this branch context;
- `make markdownlint` passing;
- `make nixie` passing;
- `make check-fmt` passing;
- `make typecheck` passing;
- `make lint` passing;
- `make test` passing;
- `docs/roadmap.md` showing item 1.1.2 as done and item 5.2.1 still open;
- the ADR, technical design, users' guide, and developers' guide agreeing that
  object tracking remains post-v1 implementation work behind a selected
  domain-owned boundary.

Expected successful command endings are ordinary zero-exit Make output. Record
the exact log paths in `Progress` when running the commands.

## Outcomes & retrospective

The implementation records ADR 008 as the durable object-tracking boundary:
post-v1 tracking should use a domain-owned `ObjectTracker` port with a simple
centroid-association default fed by detector observations. Florence-2 remains a
detection and labelling adapter, not the persistence boundary.

The documentation now signposts the decision from the technical design,
developers' guide, users' guide, roadmap, and this ExecPlan. `docs/roadmap.md`
marks item 1.1.2 complete while leaving task 5.2.1 open for later
implementation.

Validation completed with `coderabbit review --agent` returning zero findings
on the final run, and `make markdownlint`, `make nixie`, `make check-fmt`,
`make lint`, `make typecheck`, and `make test` all passing. The implementation
commit is `d52976f` (`Record object-tracking boundary`) after rebasing onto
`origin/main`.
