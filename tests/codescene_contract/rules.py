"""The CV-005 judgements on workflows a pull request can reach.

Each function returns the reasons a workflow fails; an empty list means it
complies. Returning reasons lets the fixture cases assert which clause fired,
so a rule failing for the wrong reason cannot pass as one that works.
"""

from __future__ import annotations

from codescene_contract import reader
from codescene_contract.text import computes_a_secret, folded

UPLOAD_ACTION = "leynos/shared-actions/.github/actions/upload-codescene-coverage"
COVERAGE_ACTION = "leynos/shared-actions/.github/actions/generate-coverage"
ACCESS_TOKEN = "CS_ACCESS_TOKEN"  # noqa: S105 - the secret's name, not its value
ACCESS_TOKEN_FOLDED = ACCESS_TOKEN.lower()
COVERAGE_CLI = "cs-coverage"
CODESCENE_HOST = "codescene.io"
# The variable the retired installer-digest refresher wrote, case-folded.
CLI_DIGEST_VARIABLE = "codescene_cli_sha256"


def normalized(text: str) -> str:
    """Collapse every run of whitespace to one space."""
    return " ".join(text.split())


def input_value(step: reader.Mapping, key: str) -> object:
    """Return a step's ``with`` input as written."""
    return reader.get(reader.as_mapping(reader.get(step, "with")), key)


def input_str(step: reader.Mapping, key: str) -> str | None:
    """Return a step's ``with`` input when it is a string."""
    value = input_value(step, key)
    return value if isinstance(value, str) else None


def input_is(step: reader.Mapping, key: str, *, expected: bool) -> bool:
    """Read an input as a boolean, accepting the string and native forms."""
    value = input_value(step, key)
    return value is expected or value == str(expected).lower()


def is_coverage(step: reader.Mapping) -> bool:
    """Return whether a step runs the shared coverage action."""
    return (reader.uses(step) or "").lower().startswith(COVERAGE_ACTION)


def is_upload_action(step: reader.Mapping) -> bool:
    """Return whether a step runs the upload action, in any mode."""
    return (reader.uses(step) or "").lower().startswith(UPLOAD_ACTION)


def is_upload(step: reader.Mapping) -> bool:
    """Return whether a step uploads through the action.

    ``upload`` is the action's default mode, so an absent mode is an upload,
    and ``check`` is not one: it gates changed lines and publishes nothing.
    """
    return is_upload_action(step) and input_str(step, "mode") in {None, "upload"}


def runs_the_cli(step: reader.Mapping) -> bool:
    """Return whether a step's ``run`` body names the CodeScene CLI."""
    return COVERAGE_CLI in (reader.get_str(step, "run") or "")


def _document_findings(workflow: object) -> list[str]:
    """Return the findings that search the whole parsed document.

    Every scalar is read, the host case-folded, so a workflow-level
    ``defaults.run.shell``, a ``workflow_call`` secret declaration or any other
    place a value can sit is searched without a clause naming it.
    """
    text = folded(workflow)
    findings = []
    if ACCESS_TOKEN_FOLDED in text:
        findings.append(f"a pull-request lane receives {ACCESS_TOKEN}")
    if computes_a_secret(text):
        findings.append("a pull-request lane reaches a secret by a computed name")
    if CODESCENE_HOST in text:
        findings.append(f"a pull-request lane contacts {CODESCENE_HOST}")
    return findings


def _step_findings(step: reader.Mapping) -> list[str]:
    """Return the findings for one step of a pull-request lane."""
    findings = []
    if is_upload_action(step):
        findings.append(f"a pull-request lane invokes {UPLOAD_ACTION}")
    if runs_the_cli(step):
        findings.append(f"a pull-request lane runs {COVERAGE_CLI} directly")
    if is_coverage(step) and not input_is(step, "with-ratchet", expected=True):
        findings.append("a pull-request coverage step does not set with-ratchet")
    if is_coverage(step) and not input_is(step, "publish-artefact", expected=False):
        findings.append("a pull-request coverage step publishes its report")
    if is_coverage(step) and input_value(step, "publish-baseline") not in {
        None,
        "auto",
    }:
        findings.append("a pull-request coverage step may publish its baseline")
    return findings


def pull_request_findings(workflow: object) -> list[str]:
    """Return the reasons a workflow a pull request can reach breaches CV-005."""
    findings = _document_findings(workflow)
    findings.extend(
        f"job {job_id} forwards every secret with `secrets: inherit`"
        for job_id, job in reader.jobs(workflow)
        if reader.get(job, "secrets") == "inherit"
    )
    findings.extend(
        f"job {job_id} calls `{reference}`, which resolves to no workflow here"
        for job_id, reference in reader.job_calls(workflow)
        if reader.classify_call(reference)[0] is reader.CallKind.REFUSED
    )
    for step in reader.steps(workflow):
        findings.extend(_step_findings(step))
    return findings


def stray_findings(workflow: object) -> list[str]:
    """Return the reasons a workflow other than the publisher reaches CodeScene.

    The pull-request clauses read only what a pull request can reach, and the
    publisher clauses only the publisher, so a dispatch-only or tag-triggered
    workflow would escape both. Only the publisher may hold the token, name the
    host, run the CLI or the uploader, or touch the retired installer digest.
    """
    text = folded(workflow)
    findings = [
        f"a workflow other than the publisher {reason}"
        for needle, reason in (
            (ACCESS_TOKEN_FOLDED, f"receives {ACCESS_TOKEN}"),
            (CODESCENE_HOST, f"contacts {CODESCENE_HOST}"),
            (CLI_DIGEST_VARIABLE, "reads or writes CODESCENE_CLI_SHA256"),
        )
        if needle in text
    ]
    all_steps = reader.steps(workflow)
    if any(is_upload_action(step) for step in all_steps):
        findings.append(f"a workflow other than the publisher invokes {UPLOAD_ACTION}")
    if any(runs_the_cli(step) for step in all_steps):
        findings.append(f"a workflow other than the publisher runs {COVERAGE_CLI}")
    return findings
