"""The CV-005 judgements on the push-to-``main`` publisher.

As in ``rules.py``, each function returns the reasons a workflow fails, so a
fixture case can assert which clause fired.
"""

from __future__ import annotations

from codescene_contract import reader
from codescene_contract.rules import (
    ACCESS_TOKEN,
    COVERAGE_CLI,
    input_is,
    input_str,
    is_coverage,
    is_upload,
    is_upload_action,
    normalized,
    runs_the_cli,
)
from codescene_contract.text import computes_a_secret, folded

# The expression that hands a step the secret itself. Placement clauses look
# for this rather than the bare name, because the upload's own guard names
# `env.CS_ACCESS_TOKEN` without holding anything.
SECRET_REFERENCE = "secrets.cs_access_token"  # noqa: S105 - folded, as searched
TOKEN_BINDING = "${{ secrets.CS_ACCESS_TOKEN }}"  # noqa: S105 - an expression
TOKEN_INPUT = "${{ env.CS_ACCESS_TOKEN }}"  # noqa: S105 - an expression, not a value
MAIN_REF_GUARD = "github.ref == 'refs/heads/main'"
PULL_REQUEST_GUARD = "github.event_name == 'pull_request'"


def publishes_from_main(workflow: object) -> bool:
    """Return whether a push restricted to ``main`` triggers the workflow.

    A push with no branch filter fires on every branch, so the baseline it
    wrote would be whichever branch pushed last; a tag filter names no branch.
    """
    branches = reader.get(
        reader.as_mapping(reader.trigger(workflow, "push")), "branches"
    )
    return (
        isinstance(branches, list)
        and bool(branches)
        and all(branch == "main" for branch in branches)
    )


def _unquoted(body: str) -> str:
    """Blank every character inside a single-quoted literal, keeping quotes."""
    in_quote = False
    blanked = []
    for character in body:
        if character == "'":
            in_quote = not in_quote
            blanked.append(character)
        else:
            blanked.append(" " if in_quote else character)
    return "".join(blanked)


def conjuncts(condition: str) -> list[str] | None:
    """Return the conjuncts of an ``if:`` condition, or ``None`` if it has ``||``.

    Quoted literals are blanked before the operators are looked for, so a
    ``||`` inside a string does not count and an ``&&`` inside one does not
    split. A disjunction anywhere makes every conjunct optional, which is why
    it is refused rather than parsed.
    """
    body = condition.strip()
    if body.startswith("${{") and body.endswith("}}"):
        body = body[3:-2]
    blanked = _unquoted(body)
    if "||" in blanked:
        return None
    parts, start = [], 0
    index = blanked.find("&&")
    while index != -1:
        parts.append(body[start:index])
        start = index + 2
        index = blanked.find("&&", start)
    parts.append(body[start:])
    return [normalized(part) for part in parts]


def _guarded_by(step: reader.Mapping, guard: str) -> bool:
    """Return whether a step's condition carries ``guard`` as a conjunct."""
    parts = conjuncts(reader.get_str(step, "if") or "")
    return parts is not None and guard in parts


def _binds_the_token(step: reader.Mapping) -> bool:
    """Return whether a step binds the token in its own ``env``, as the secret.

    Asserted positively because the guard ``env.CS_ACCESS_TOKEN != ''`` reads a
    missing binding as empty: with the binding deleted the upload skips forever
    and nothing fails.
    """
    value = reader.get(reader.as_mapping(reader.get(step, "env")), ACCESS_TOKEN)
    return isinstance(value, str) and normalized(value) == TOKEN_BINDING


def _forwards_the_token(job: reader.Mapping) -> bool:
    """Return whether a job calling a reusable workflow hands it the token."""
    if reader.get(job, "uses") is None:
        return False
    return reader.get(job, "secrets") == "inherit" or any(
        SECRET_REFERENCE in folded(reader.get(job, key)) for key in ("with", "secrets")
    )


def _wide_token_findings(workflow: object) -> list[str]:
    """Return the reasons the token is declared in a scope wider than a step."""
    findings = []
    if SECRET_REFERENCE in folded(reader.get(reader.as_mapping(workflow), "env")):
        findings.append(f"the publisher declares {ACCESS_TOKEN} for every job")
    for job_id, job in reader.jobs(workflow):
        if SECRET_REFERENCE in folded(reader.get(job, "env")):
            findings.append(f"job {job_id} declares {ACCESS_TOKEN} for every step")
        if _forwards_the_token(job):
            findings.append(
                f"job {job_id} forwards {ACCESS_TOKEN} to a reusable workflow"
            )
    return findings


def _token_findings(workflow: object) -> list[str]:
    """Return the reasons the token reaches somewhere other than the upload.

    "Some step has the token" proves nothing: moving it to the coverage step
    satisfies that while the upload's guard goes false. So the upload must bind
    it, no other step may hold it, and no wider scope may declare it.
    """
    findings = _wide_token_findings(workflow)
    if computes_a_secret(folded(workflow)):
        findings.append("the publisher reaches a secret by a computed name")
    for step in reader.steps(workflow):
        if is_upload(step) and not _binds_the_token(step):
            findings.append(f"the upload step does not bind {ACCESS_TOKEN} in its env")
        if not is_upload(step) and SECRET_REFERENCE in folded(step):
            findings.append(f"a step other than the upload receives {ACCESS_TOKEN}")
    return findings


def _concurrency_findings(workflow: object) -> list[str]:
    """Return the reasons the publisher's runs could cancel or displace one another.

    A cancelled publisher abandons both its upload and its baseline write. Any
    ``cancel-in-progress`` other than an absent key or a literal ``false`` is
    refused, an expression included. GitHub also keeps one pending run per
    group and a newer arrival replaces it, so a dispatch sharing the pushes'
    group could replace a pending push, and a dispatch never advances the
    baseline: a dispatchable publisher's group must name the event.
    """
    group = reader.get(reader.as_mapping(workflow), "concurrency")
    findings = (
        [] if group is not None else ["the publisher declares no concurrency group"]
    )
    blocks = [
        block
        for block in (
            group,
            *(reader.get(job, "concurrency") for _, job in reader.jobs(workflow)),
        )
        if block is not None
    ]
    findings.extend(
        "the publisher may cancel a run in progress"
        for block in blocks
        if reader.get(reader.as_mapping(block), "cancel-in-progress")
        not in {None, False}
    )
    if _is_dispatchable(workflow):
        findings.extend(
            "a dispatch can replace a pending push in the publisher's group"
            for block in blocks
            if not _separates_events(block)
        )
    return findings


def _is_dispatchable(workflow: object) -> bool:
    """Return whether anything other than a push can start the workflow."""
    return any(name != "push" for name in reader.trigger_names(workflow))


def _separates_events(block: object) -> bool:
    """Return whether a concurrency block's group names the triggering event."""
    group = (
        block
        if isinstance(block, str)
        else reader.get_str(reader.as_mapping(block), "group")
    )
    return group is not None and "github.event_name" in group


def _reachability_findings(workflow: object) -> list[str]:
    """Return the reasons the publisher's required work might never run.

    A requirement met by a step that cannot run is not met: a step or job behind
    ``if: false`` reads as present to every other clause. So no publisher job
    may carry a condition, the ratcheted coverage step must carry none, and the
    upload is read only from the action, never from a ``run`` body, where
    ``false && cs-coverage upload`` still contains the command.
    """
    findings = [
        f"publisher job {job_id} carries an `if:`"
        for job_id, job in reader.jobs(workflow)
        if reader.get(job, "if") is not None
    ]
    all_steps = reader.steps(workflow)
    if not any(
        is_coverage(step)
        and input_is(step, "with-ratchet", expected=True)
        and reader.get(step, "if") is None
        for step in all_steps
    ):
        findings.append("the main publisher generates no ratcheted coverage")
    if any(runs_the_cli(step) for step in all_steps):
        findings.append(
            f"the publisher runs {COVERAGE_CLI} directly rather than through the action"
        )
    return findings


def publisher_findings(workflow: object) -> list[str]:
    """Return the reasons a main publisher fails to publish what CV-005 requires."""
    findings = _reachability_findings(workflow)
    uploads = [step for step in reader.steps(workflow) if is_upload(step)]
    if not uploads:
        findings.append("the main publisher uploads nothing to CodeScene")
    if any(not _guarded_by(step, MAIN_REF_GUARD) for step in uploads):
        findings.append(f"an upload step is not guarded by `{MAIN_REF_GUARD}`")
    findings.extend(_token_findings(workflow))
    findings.extend(_concurrency_findings(workflow))
    return findings


def wiring_findings(workflow: object) -> list[str]:
    """Return the reasons the publisher's upload would not send what it measured.

    Each upload must read the file, in the format, that a coverage step writes,
    and pass the token its step binds as its ``access-token``, or its guard
    holds while the action runs unauthenticated.
    """
    all_steps = reader.steps(workflow)
    written = [
        (input_str(step, "output-path"), input_str(step, "format"))
        for step in all_steps
        if is_coverage(step)
    ]
    findings = []
    for upload in (step for step in all_steps if is_upload_action(step)):
        read = (input_str(upload, "path"), input_str(upload, "format"))
        if read not in written:
            findings.append(
                f"the upload reads {read}, which no coverage step writes; "
                f"written: {written}"
            )
        token = input_str(upload, "access-token")
        if token is None or normalized(token) != TOKEN_INPUT:
            findings.append(
                f"the upload's access-token is {token!r}, not the token its step binds"
            )
    return findings


def second_writer_findings(workflow: object) -> list[str]:
    """Return the reasons a non-publisher workflow could write the baseline.

    The shared action saves the ratchet baseline on any push to ``main`` that
    runs a ratcheted coverage step, so a pull-request workflow that also runs
    on push would race the publisher for the baseline every pull request is
    measured against. Its coverage steps must carry the pull-request guard as a
    conjunct. A workflow that neither runs on push nor can be called cannot
    write at all.
    """
    # A reusable workflow inherits its caller's event, so a call made on a push
    # to `main` runs its coverage step as a push.
    if not {"push", "workflow_call"} & set(reader.trigger_names(workflow)):
        return []
    return [
        "a ratcheted coverage step can run on push without "
        f"`{PULL_REQUEST_GUARD}` and would write the baseline"
        for step in reader.steps(workflow)
        if is_coverage(step)
        and input_is(step, "with-ratchet", expected=True)
        and not _guarded_by(step, PULL_REQUEST_GUARD)
    ]


def second_writers(all_workflows: reader.Workflows) -> list[str]:
    """Return each ratcheted coverage step a push can run outside the publisher.

    Seeds are the workflows a push starts, other than the publisher; the
    closure then takes in every local workflow they call, since a callee runs
    with its caller's push. Each entry names the workflow and the finding.
    """
    seeds = {
        name
        for name, workflow in all_workflows.items()
        if "push" in reader.trigger_names(workflow)
        and not publishes_from_main(workflow)
    }
    return [
        f"{name}: {finding}"
        for name in sorted(reader.closure_from(all_workflows, seeds))
        if not publishes_from_main(all_workflows[name])
        for finding in second_writer_findings(all_workflows[name])
    ]
