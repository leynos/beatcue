# Resolve BeatCue Logisphere design-stage review

This ExecPlan (execution plan) is a living document. The sections
`Constraints`, `Tolerances`, `Risks`, `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work
proceeds.

Status: COMPLETE

## Purpose / big picture

The Logisphere design-stage review identified several issues that should be
resolved before implementation begins. The highest-priority concerns are:
define `AnalysisResult`, draw the v1 boundary explicitly, decide the BeatCue
JSON schema technology now, add input-size bounds, and add a walking-skeleton
task to phase 1. The review names these as recommended next steps in
`docs/beatcue-logisphere-design-stage-review.md` §8, and ties them to design
flaws, unresolved risks, and pre-mortem scenarios in §§3-7.

After this plan is executed, a reviewer should be able to open
`docs/beatcue-technical-design.md` and `docs/roadmap.md` and see a credible
v1 design boundary: a defined canonical result object, a chosen schema
technology, explicit resource limits, and an early real-I/O walking skeleton
that proves the architecture before deeper feature work. No production code is
part of this plan; the observable result is a tighter, implementable design and
roadmap.

Implementation must not begin until this draft ExecPlan is explicitly approved.

## Constraints

- Modify documentation only unless the user explicitly approves implementation
  work. The intended files are `docs/beatcue-technical-design.md`,
  `docs/roadmap.md`, and this ExecPlan.
- Keep the review priorities first. Lower-priority findings from
  `docs/beatcue-logisphere-design-stage-review.md` may be acknowledged, but
  they must not crowd out the five requested priorities.
- Preserve the existing hexagonal architecture decision unless the user asks to
  reopen it. The design-stage review says the current procedural pipeline is
  the right v1 choice even though a pipeline-as-DAG alternative may become
  useful later; see `docs/beatcue-logisphere-design-stage-review.md` §5.
- Keep v1 deterministic and credible. Semantic annotation, object tracking,
  remote model execution, GPU scheduling, and advanced tracking should be
  framed as post-v1 unless the user explicitly widens v1 scope.
- Define the v1 input target as single-scene or single-shot videos. The design
  must not optimize for feature-length continuous takes, including edge cases
  like _Russian Ark_, unless a later plan explicitly widens the target.
- Follow `docs/documentation-style-guide.md`: British English with Oxford
  spelling, sentence-case headings, wrapped prose, fenced code language
  identifiers, and Markdown table captions.
- Do not edit `docs/beatcue-logisphere-design-stage-review.md`; it is review
  evidence, not a design source to rewrite.
- Do not start implementation tasks from `docs/roadmap.md`. This plan is for
  resolving design-stage documentation concerns.

## Tolerances (exception triggers)

- Scope: if resolving the five priority concerns requires changing more than
  three documentation files besides this ExecPlan, stop and ask whether to
  widen the documentation update.
- Size: if the net documentation change exceeds 900 lines, stop and split the
  work or ask for approval to continue.
- Schema decision: if choosing `msgspec` conflicts with project policy,
  dependency availability, or Python 3.14 compatibility, stop and present
  alternatives before changing the design.
- V1 boundary: if a credible v1 cannot be described without including semantic
  annotation or object tracking, stop and ask whether the product boundary
  should be widened.
- Resource bounds: if no defensible default input bound can be stated for
  single-scene or single-shot videos, stop and propose two bounded options.
- Validation: if `make markdownlint` or `make nixie` fails after two fix
  attempts, stop and report the failure with log paths.

## Risks

- Risk: Selecting schema technology in documentation may imply a new runtime
  dependency before implementation has benchmarked it.
  Severity: medium
  Likelihood: medium
  Mitigation: choose `msgspec` as a design decision with an explicit escape
  hatch: if the walking skeleton proves it unsuitable, the implementation must
  update the ADR/design before continuing. The current project lint aliases
  already mention `msgspec`, and the review says the decision is blocking, not
  truly deferred; see `docs/beatcue-logisphere-design-stage-review.md` §3.4
  and §7 finding 7.

- Risk: Drawing v1 too narrowly may appear to remove headline features from
  BeatCue.
  Severity: medium
  Likelihood: medium
  Mitigation: state that v1 is deterministic cue extraction and agent-native
  operation, while semantic/object enrichment remains explicitly post-v1. The
  review says the 80/20 product is useful and should be framed as a viable
  standalone deliverable; see
  `docs/beatcue-logisphere-design-stage-review.md` §3.2 and §8.

- Risk: Input-size bounds may be mistaken for permanent product limits.
  Severity: low
  Likelihood: medium
  Mitigation: phrase bounds as v1 default support and specify degradation
  paths for larger files, including lower sample rates, windowed processing,
  or explicit refusal. The memory-exhaustion pre-mortem in
  `docs/beatcue-logisphere-design-stage-review.md` §4 scenario B provides the
  rationale.

- Risk: A walking-skeleton task could duplicate later media-adapter tasks.
  Severity: low
  Likelihood: medium
  Mitigation: define the skeleton as a deliberately narrow proof:
  `ffprobe` -> sample one frame -> write one WebVTT cue through the intended
  boundaries. It validates plumbing, not full feature extraction. The review
  recommends this exact mitigation in
  `docs/beatcue-logisphere-design-stage-review.md` §4 scenario A and §8.

## Progress

- [x] (2026-05-09 10:52Z) Read repository state, current branch, Logisphere
  review, roadmap, technical design, and ExecPlan instructions.
- [x] (2026-05-09 10:58Z) Draft this ExecPlan at
  `docs/execplans/resolve-beatcue-logisphere-design-stage-review.md`.
- [x] (2026-05-09 11:06Z) Received explicit approval to implement the
  planned documentation revisions.
- [x] (2026-05-09 11:14Z) Updated `docs/beatcue-technical-design.md` with
  `AnalysisResult`, v1 boundary, schema decision, and input-size/resource
  bounds.
- [x] (2026-05-09 11:14Z) Updated `docs/roadmap.md` with a phase 1
  walking-skeleton task and dependency adjustments required by the new v1
  boundary.
- [x] (2026-05-09 11:14Z) Checked `README.md`, `docs/users-guide.md`, and
  `docs/developers-guide.md` for consistency; only user/developer guide
  boundary and schema wording needed patching.
- [x] (2026-05-09 11:17Z) Validated Markdown and Mermaid diagrams with
  `make markdownlint` and `make nixie`.
- [x] (2026-05-09 11:20Z) Commit and push the documentation updates after
  approval and validation.

## Surprises & discoveries

- Observation: `docs/beatcue-logisphere-design-stage-review.md` already
  reflects the recent two-pass semantic ordering fix.
  Evidence: the review proposal summary describes a "two-pass
  action-intensity pipeline (deterministic first, then semantic enrichment)" in
  §1.
  Impact: this plan does not need to address the previous ordering issue and
  can focus on the five requested priorities.

- Observation: `docs/roadmap.md` already has task 1.1.1 for schema selection,
  but `docs/beatcue-technical-design.md` still lists the schema mechanism as a
  deferred decision.
  Evidence: `docs/roadmap.md` task 1.1.1 says to record the v1 schema decision;
  `docs/beatcue-technical-design.md` §21 says the canonical schema technology
  is deferred.
  Impact: implementation should remove that contradiction by selecting schema
  technology in the design and turning roadmap task 1.1.1 into an ADR or
  ratification task for the chosen decision.

- Observation: The supporting user and developer guides described planned
  semantic, object, and OTIO capabilities without the new v1 boundary.
  Evidence: `docs/users-guide.md` included `--caption-model`, `--detector`,
  `--track-objects`, and `--otio` in the primary planned command example.
  Impact: the consistency pass narrowed the main example to deterministic v1
  analysis and labelled enrichment as post-v1.

## Decision log

- Decision: Use this ExecPlan as a draft-only planning artefact and do not
  implement the review fixes until explicit approval.
  Rationale: the ExecPlan skill requires approval before execution, and the
  user specifically asked to plan the work.
  Date/Author: 2026-05-09 / Codex.

- Decision: Plan to choose `msgspec` for BeatCue JSON schema technology.
  Rationale: the review says schema technology is blocking, not deferred.
  BeatCue needs fast typed validation, deterministic JSON round-tripping, and
  Python-native model definitions that can sit beside immutable domain values.
  `msgspec.Struct` can define typed serializable structures without requiring a
  heavyweight validation framework. If later implementation evidence disproves
  this choice, the design must be revised before coding continues.
  Date/Author: 2026-05-09 / Codex.

- Decision: Plan to define v1 as deterministic cue extraction plus the
  agent-native CLI subset needed to operate it; treat semantic annotation,
  object tracking, OTIO enrichment, remote models, GPU scheduling, and advanced
  tracking as post-v1.
  Rationale: the review identifies a scope-to-team mismatch and recommends
  drawing a credible v1 boundary around the 80/20 product. See
  `docs/beatcue-logisphere-design-stage-review.md` §7 findings 2, 11, and 13,
  and §8 recommended step 2.
  Date/Author: 2026-05-09 / Codex.

- Decision: Define the v1 media target as single-scene or single-shot videos,
  not feature-length or pathological long-take inputs.
  Rationale: the user clarified that BeatCue's current target is single-scene
  or single-shot videos, with no "Russian Ark" style cheating. This makes the
  input-size bound a product boundary rather than a general-purpose film
  analysis promise.
  Date/Author: 2026-05-09 / User and Codex.

- Decision: Proceed from the approved plan without widening into production
  implementation.
  Rationale: the user explicitly asked to implement the planned revisions, and
  the plan's constraints limit this change to design and roadmap
  documentation.
  Date/Author: 2026-05-09 / Codex.

## Outcomes & retrospective

Execution resolved the five user-prioritized Logisphere design-stage concerns:

- `docs/beatcue-technical-design.md` now defines `AnalysisResult` as the
  canonical application return value and writer input.
- The design states a deterministic v1 boundary for single-scene or
  single-shot videos and labels semantic, object, OTIO, remote model, GPU, and
  advanced tracking work as post-v1.
- BeatCue JSON now selects `msgspec.Struct` as the v1 schema technology.
- The design states default v1 input bounds, sampled-frame limits, incremental
  feature extraction, feature-series retention rules, and a post-v1 semantic
  keyframe cap.
- `docs/roadmap.md` now includes a phase 1 walking skeleton that proves
  `ffprobe` -> one sampled frame -> one-cue WebVTT through the intended
  boundaries.

The supporting user and developer guides were patched only where they
conflicted with the narrowed v1 boundary. Validation passed with
`make markdownlint` and `make nixie`.

## Context and orientation

The relevant files are:

- `docs/beatcue-logisphere-design-stage-review.md`: the design-stage review
  that identifies the concerns to address. Its §8 lists the recommended next
  steps, and §§3-7 provide the supporting findings.
- `docs/beatcue-technical-design.md`: the primary design document. It defines
  the package purpose, hexagonal architecture, domain model, two-pass analysis
  pipeline, output formats, CLI surface, configuration, subprocess boundary,
  testing strategy, failure modes, and deferred decisions.
- `docs/roadmap.md`: the delivery roadmap. It currently schedules schema
  selection in task 1.1.1 and media work later, but it does not yet include the
  walking skeleton recommended by the review.
- `docs/developers-guide.md` and `docs/users-guide.md`: supporting
  documentation that should stay consistent with the v1 boundary if the
  boundary changes user-visible claims.

Terms used in this plan:

- `AnalysisResult`: the canonical in-memory object from which BeatCue JSON,
  WebVTT, and OTIO outputs are written. The review says it is missing from the
  design even though it is the most important data structure; see
  `docs/beatcue-logisphere-design-stage-review.md` §3.4 and §7 finding 1.
- v1 boundary: the explicit set of capabilities BeatCue promises for its first
  credible release. The review says the current design is too broad for a
  small team; see `docs/beatcue-logisphere-design-stage-review.md` §3.6 and
  §7 finding 2.
- Schema technology: the Python mechanism used to define and validate BeatCue
  JSON. The current design defers this decision, but the review says it blocks
  implementation; see `docs/beatcue-logisphere-design-stage-review.md` §3.4
  and §7 finding 7.
- Walking skeleton: a deliberately tiny end-to-end implementation path that
  exercises real I/O through the intended architecture. Here, it means
  `ffprobe` -> sample one frame -> write a single-cue WebVTT file through the
  hexagonal pipeline.

## Plan of work

Stage A updates the technical design. In `docs/beatcue-technical-design.md`
§7, add an `AnalysisResult` definition beside `Cue`. The definition must name
fields, invariants, and serialization behaviour. The minimum field set is:
media metadata, cues, diagnostics, configuration snapshot, provenance,
feature summaries, and an optional bounded feature-series attachment. State
that writers consume `AnalysisResult` and that BeatCue JSON is the lossless
serialization of it.

In the same file, remove the schema mechanism from §21 deferred decisions and
add a design decision near the output-format or domain-model discussion:
BeatCue JSON uses `msgspec.Struct` definitions as the schema technology for
v1. Explain that `msgspec` defines typed serializable structures, supports
fast JSON encoding and decoding, and keeps validation close to the domain data
model. Note that a future change must update the design or an ADR before
replacing it.

Also in `docs/beatcue-technical-design.md`, add a short v1 boundary section.
Place it after goals/non-goals or before implementation phases. State that v1
contains deterministic cue extraction, BeatCue JSON, WebVTT, `inspect`,
`analyse`, `agent-context`, profiles/configuration sufficient for deterministic
runs, and failure diagnostics. State that semantic annotation, object
tracking, OTIO enrichment, remote models, GPU scheduling, and advanced tracking
are post-v1 unless a later ADR changes the boundary. Cite the Logisphere
scope-to-team finding in `docs/beatcue-logisphere-design-stage-review.md` §7
finding 2 and the 80/20 finding in §7 finding 13.

Still in the technical design, add input-size and memory-budget guidance.
Place it near §10 feature extraction or §18 failure modes. Define v1 default
support as single-scene or single-shot videos, not full films or pathological
long-take inputs. State concrete default bounds for that target, for example a
maximum duration, resolution tier, and sample-frame budget under the default
`sample_fps = 4.0`. State that longer, higher-resolution, or multi-scene inputs
must either lower sample rate, process in windows, or fail early with an
actionable error. Feature computation must be incremental, and full
feature-series retention must stay disabled unless `--include-series` is set.
Add a cap on selected semantic keyframes for post-v1 semantic runs so model
inference cannot grow without bound. Cite
`docs/beatcue-logisphere-design-stage-review.md` §4 scenario B and §7 findings
5, 6, and 16.

Stage B updates the roadmap. In `docs/roadmap.md`, add a walking-skeleton task
to phase 1. Prefer a new step after the package skeleton and before shared
fixtures, for example `### 1.3. Prove real I/O through a walking skeleton`,
then renumber the existing fixture step if necessary. The task must require
`ffprobe`, sample one frame, create one synthetic cue, and write a WebVTT file
through the intended domain/application/adapter boundaries. It must cite
`docs/beatcue-logisphere-design-stage-review.md` §4 scenario A and
`docs/beatcue-logisphere-design-stage-review.md` §8 recommended step 5.

In the roadmap, adjust task 1.1.1 so it no longer asks implementers to decide
between JSON Schema, msgspec, and Pydantic. It should instead record or ratify
the chosen `msgspec` schema decision as an ADR if ADRs are still desired. Make
dependent tasks cite the updated design section. Update phase descriptions to
state the explicit v1 boundary and that deterministic-only BeatCue is a useful
standalone product.

Stage C checks supporting docs for consistency. Read `README.md`,
`docs/users-guide.md`, and `docs/developers-guide.md` for claims that conflict
with the new v1 boundary or schema decision. Patch only conflicting text. Do
not expand scope into broad documentation rewrites.

Stage D validates and commits. Run `make fmt` on all Markdown files immediately
after documentation changes, then run `make markdownlint` and `make nixie`
through `tee` logs in `/tmp`. Commit with a file-based commit message after
gates pass. Push the branch after the commit.

## Concrete steps

From the repository root, confirm the active branch and working-tree state:

```bash
git branch --show
git status --short
```

Expected output starts with the active branch name and then no unexpected
working-tree changes:

```plaintext
<active-branch-name>
```

Then edit the documentation files using `apply_patch`. Do not use scripts for
semantic rewrites. Keep the changes narrow and cite review sections directly
in prose where appropriate.

After edits, inspect the changed hunks:

```bash
git --no-pager diff --no-ext-diff -- docs/beatcue-technical-design.md docs/roadmap.md
```

Run gates with durable logs:

```bash
make fmt 2>&1 | tee /tmp/fmt-logisphere-plan-beatcue-initial-design.out
make markdownlint 2>&1 | tee /tmp/markdownlint-logisphere-plan-beatcue-initial-design.out
make nixie 2>&1 | tee /tmp/nixie-logisphere-plan-beatcue-initial-design.out
```

Expected successful endings:

```plaintext
Summary: 0 error(s)
```

and:

```plaintext
All diagrams validated successfully!
```

Then revert any unrelated formatting drift before committing.

Commit using a file-based commit message:

```bash
COMMIT_MSG_DIR=$(mktemp -d)
cat > "$COMMIT_MSG_DIR/COMMIT_MSG.md" << 'ENDOFMSG'
Resolve BeatCue design-stage priorities

Define the canonical analysis result, v1 boundary, schema decision, resource
bounds, and phase 1 walking skeleton needed to address the Logisphere
design-stage review priorities.
ENDOFMSG
git commit -F "$COMMIT_MSG_DIR/COMMIT_MSG.md"
rm -rf "$COMMIT_MSG_DIR"
```

Push:

```bash
git push
```

## Validation and acceptance

The documentation update is accepted when:

- `docs/beatcue-technical-design.md` defines `AnalysisResult` with fields,
  invariants, and serialization responsibility.
- `docs/beatcue-technical-design.md` explicitly states the v1 boundary and
  post-v1 scope.
- `docs/beatcue-technical-design.md` selects `msgspec` as the BeatCue JSON
  schema technology and no longer lists schema technology as deferred.
- `docs/beatcue-technical-design.md` states that v1 targets single-scene or
  single-shot videos, excludes feature-length long-take cases from default
  support, defines input-size/resource bounds, describes memory behaviour for
  feature series, and sets a semantic keyframe cap for semantic runs.
- `docs/roadmap.md` contains a phase 1 walking-skeleton task that proves
  `ffprobe` -> one sampled frame -> one-cue WebVTT through the intended
  architecture.
- `docs/roadmap.md` no longer frames schema technology as an undecided
  comparison task.
- Any changed README, users' guide, or developer guide text remains consistent
  with the new v1 boundary.
- `make markdownlint` and `make nixie` pass.

The update does not need to run Python tests because it is documentation-only.
If implementation files change despite the constraint, stop and run the full
Python gate set only after documenting the constraint violation and receiving
approval.

## Idempotence and recovery

The documentation edits are safe to repeat. If a patch applies partially, use
`git status --short` and `git --no-pager diff --no-ext-diff` to inspect the
current state, then reapply only missing hunks. If `make fmt` changes unrelated
Markdown files, revert those unrelated hunks manually with `apply_patch`; do
not use destructive checkout commands unless explicitly instructed.

If the schema decision proves controversial during review, keep the v1
boundary, `AnalysisResult`, input bounds, and walking-skeleton task, but change
the schema section into a short ADR-required decision point only after the user
approves that revision.

## Artifacts and notes

The most important source evidence is:

```plaintext
docs/beatcue-logisphere-design-stage-review.md §8:
1. Define AnalysisResult in §7.
2. Draw the v1 boundary explicitly.
3. Decide the schema technology now, not later.
4. Add input-size bounds or memory-budget guidance.
5. Add a walking-skeleton task to phase 1.
```

The current contradiction to resolve is:

```plaintext
docs/roadmap.md task 1.1.1: Record the v1 schema decision for BeatCue JSON.
docs/beatcue-technical-design.md §21: The canonical schema technology is deferred.
```

The desired result is one consistent story: `msgspec` is selected for v1,
`AnalysisResult` is the canonical object, and the roadmap proves real media I/O
early.

## Interfaces and dependencies

The plan selects these interfaces and dependencies for the design update:

- `AnalysisResult` is a domain value object in `beatcue.domain` when
  implemented. It contains media metadata, cues, diagnostics, configuration
  snapshot, provenance, feature summaries, and optional bounded feature series.
- BeatCue JSON is defined by `msgspec.Struct` schema types when implemented.
  The design should not require implementation in this planning pass, but the
  contract should be explicit enough that later code can follow it.
- The walking skeleton should eventually exercise the same boundary names
  already used in the design: `MediaProbe`, `FrameSampler`, `CueWriter`, and
  `AnalyseVideo`.
- The walking skeleton output is a valid WebVTT file with one metadata cue.

## Revision note

Initial draft created 2026-05-09. It scopes the Logisphere review response to
the five user-prioritized concerns, selects `msgspec` as the planned schema
technology, and requires approval before implementation.

Revision 2026-05-09: updated the v1 resource-bound guidance to reflect the
user clarification that BeatCue currently targets single-scene or single-shot
videos, not feature-length or pathological long-take inputs. The remaining
implementation work should use that target when defining input-size and memory
limits.
