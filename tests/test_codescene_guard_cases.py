"""Drive the publisher's exact guard, pinned group and pinned triggers.

Split from ``test_codescene_publisher_cases.py`` under the repository's
400-line cap. Each case is a condition, group or trigger set that the looser
readings passed.
"""

from __future__ import annotations

import pytest
from codescene_contract import publisher_rules
from codescene_contract.token_check import CHECK_COMMAND
from test_codescene_publisher_cases import (
    AVAILABLE,
    GUARD,
    NEVER_CANCEL,
    parse,
    publisher,
)


@pytest.mark.parametrize(
    "upload_if",
    [
        f"${{{{ {AVAILABLE} && github.ref == 'refs/heads/main' && false }}}}",
        (
            f"${{{{ {AVAILABLE} && github.ref == 'refs/heads/main'"
            " && github.ref == 'refs/heads/develop' }}"
        ),
        (
            f"${{{{ {AVAILABLE} && !(github.actor == 'x'"
            " && github.ref == 'refs/heads/main' && true) }}"
        ),
    ],
    ids=["never_true", "second_ref", "negated_group"],
)
def test_a_guard_that_stops_or_inverts_the_upload_is_refused(upload_if: str) -> None:
    """A conjunct beside the two guards can only narrow, defeat or invert."""
    findings = publisher_rules.publisher_findings(parse(publisher(upload_if=upload_if)))
    assert len(findings) == 1, findings
    assert "not guarded" in findings[0], findings


@pytest.mark.parametrize(
    "group",
    [
        "${{ github.workflow }}-${{ github.ref }}-${{ github.event_name }}",
        "${{ github.workflow }}-${{ github.event_name }}",
        "${{ github.workflow }}-github.ref",
        "pub-${{ github.ref }}",
    ],
    ids=["keyed_on_the_event_too", "keyed_on_the_event_only", "literal_ref", "renamed"],
)
def test_the_group_is_exactly_the_workflow_and_ref(group: str) -> None:
    """Any other group lets a push and a dispatch overlap, or keys nothing."""
    concurrency = f"concurrency:\n  group: {group}\n  cancel-in-progress: false"
    findings = publisher_rules.publisher_findings(
        parse(publisher(concurrency=concurrency))
    )
    assert len(findings) == 1, findings
    assert "not exactly" in findings[0], findings


def test_spacing_inside_the_group_is_not_its_shape() -> None:
    """The group is compared with its whitespace removed."""
    concurrency = (
        "concurrency:\n  group: ${{github.workflow}}-${{  github.ref  }}\n"
        "  cancel-in-progress: false"
    )
    assert not publisher_rules.publisher_findings(
        parse(publisher(concurrency=concurrency))
    )


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        (
            "  coverage:\n",
            "  coverage:\n    concurrency:\n      group: upload\n",
            "not exactly",
        ),
        (
            "  workflow_dispatch:\n",
            "  workflow_dispatch:\n  schedule:\n    - cron: '0 0 * * *'\n",
            "not exactly",
        ),
        ("  workflow_dispatch:\n", "", "not exactly"),
    ],
    ids=["constant_job_group", "schedule_added", "dispatch_dropped"],
)
def test_the_job_group_and_triggers_are_pinned(
    old: str, new: str, expected: str
) -> None:
    """A constant job group, or a changed trigger set, is named."""
    source = publisher(NEVER_CANCEL, GUARD)
    assert source.count(old) == 1, old
    findings = publisher_rules.publisher_findings(parse(source.replace(old, new)))
    assert len(findings) == 1, findings
    assert expected in findings[0], findings


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        (
            "      - id: codescene-token\n",
            "      - id: codescene-token\n        if: always()\n",
            "carries an `if:`",
        ),
        ("      - id: codescene-token\n        run:", "      - run:", "has no id"),
        (
            "      - id: codescene-token\n",
            "      - id: codescene-token\n        shell: bash -c 'exit 0; {0}'\n",
            "declares `shell`",
        ),
        (
            "      - id: codescene-token\n",
            "      - id: codescene-token\n        continue-on-error: true\n",
            "declares `continue-on-error`",
        ),
        ("secrets.CS_ACCESS_TOKEN != ''", "true", "exactly one token check step"),
        (
            f"      - id: codescene-token\n        run: {CHECK_COMMAND}\n",
            "",
            "exactly one token check step",
        ),
        (
            AVAILABLE,
            "env.CS_ACCESS_TOKEN != ''",
            "not guarded",
        ),
        (
            AVAILABLE,
            "steps.other.outputs.available == 'true'",
            "not guarded",
        ),
    ],
    ids=[
        "check_behind_an_if",
        "check_without_an_id",
        "check_behind_a_shell",
        "check_allowed_to_fail",
        "check_command_changed",
        "check_deleted",
        "guard_on_the_environment",
        "guard_on_another_step",
    ],
)
def test_the_token_check_is_exact(old: str, new: str, expected: str) -> None:
    """A skippable, unreadable or altered check, or a guard off it, is named."""
    source = publisher()
    assert old in source, old
    findings = publisher_rules.publisher_findings(parse(source.replace(old, new, 1)))
    assert any(expected in finding for finding in findings), findings


@pytest.mark.parametrize(
    "line",
    [
        "          installer-checksum: '0'\n",
        "          installer-checksum: ${{ vars.CODESCENE_CLI_SHA256 }}\n",
    ],
    ids=["input", "variable"],
)
def test_the_retired_digest_is_refused_in_the_publisher(line: str) -> None:
    """The retired digest on the upload step is named on the publisher too."""
    source = publisher().replace(
        "          access-token:", line + "          access-token:"
    )
    findings = publisher_rules.publisher_findings(parse(source))
    assert len(findings) == 1, findings
    assert "retired installer digest" in findings[0], findings


# The token check step as the publisher fixture writes it.
TOKEN_CHECK = f"      - id: codescene-token\n        run: {CHECK_COMMAND}\n"


@pytest.mark.parametrize(
    "placed",
    [
        "@REST@" + TOKEN_CHECK,
        "@REST@  token:\n    steps:\n" + TOKEN_CHECK,
    ],
    ids=["after_the_upload", "in_another_job"],
)
def test_the_token_check_precedes_the_upload_in_its_job(placed: str) -> None:
    """A check the upload cannot read, later or in another job, is named alone.

    A ``steps.<id>`` output resolves only later in the same job, so either
    placement leaves the upload skipped on every push.
    """
    source = publisher()
    assert TOKEN_CHECK in source
    moved = placed.replace("@REST@", source.replace(TOKEN_CHECK, "", 1))
    findings = publisher_rules.publisher_findings(parse(moved))
    assert len(findings) == 1, findings
    assert "before every upload" in findings[0], findings


# A shell that runs nothing, so a step under it never writes its output.
SILENT_SHELL = "shell: bash -c 'exit 0; {0}'"


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ("jobs:\n", f"defaults:\n  run:\n    {SILENT_SHELL}\njobs:\n", True),
        (
            "  coverage:\n",
            f"  coverage:\n    defaults:\n      run:\n        {SILENT_SHELL}\n",
            True,
        ),
        (
            "jobs:\n",
            (
                f"jobs:\n  other:\n    defaults:\n      run:\n        {SILENT_SHELL}\n"
                "    steps:\n      - run: 'true'\n"
            ),
            False,
        ),
    ],
    ids=["workflow_default_shell", "job_default_shell", "other_job_default_shell"],
)
def test_the_token_check_runs_under_no_inherited_shell(
    old: str, new: str, *, expected: bool
) -> None:
    """A default shell over the check is named; one on another job is not.

    A workflow or job ``defaults.run.shell`` wraps the check as a step
    ``shell`` would, so the check never answers and the upload skips.
    """
    source = publisher()
    assert old in source, old
    findings = publisher_rules.publisher_findings(parse(source.replace(old, new, 1)))
    if expected:
        assert len(findings) == 1, findings
        assert "defaults.run.shell" in findings[0], findings
    else:
        assert not findings, findings


def test_a_check_between_two_uploads_is_refused() -> None:
    """A check after the first of two uploads is named.

    With one upload only, a rule that read just the last upload would pass.
    """
    head, upload = publisher().split(TOKEN_CHECK)
    findings = publisher_rules.publisher_findings(
        parse(head + upload + TOKEN_CHECK + upload)
    )
    assert len(findings) == 1, findings
    assert "before every upload" in findings[0], findings


def test_a_check_before_two_uploads_is_accepted() -> None:
    """A check before both of two uploads is not named: the rule stays narrow."""
    head, upload = publisher().split(TOKEN_CHECK)
    findings = publisher_rules.publisher_findings(
        parse(head + TOKEN_CHECK + upload + upload)
    )
    assert not findings, findings
