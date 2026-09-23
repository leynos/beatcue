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
    """Any other group lets uploads land out of commit order, or keys nothing."""
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
