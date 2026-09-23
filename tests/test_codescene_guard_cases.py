"""Drive the publisher's exact guard, keyed group and pinned triggers.

Split from ``test_codescene_publisher_cases.py`` under the repository's
400-line cap. Each case is a condition, group or trigger set that the looser
readings passed.
"""

from __future__ import annotations

import pytest
from codescene_contract import publisher_rules
from test_codescene_publisher_cases import GUARD, NEVER_CANCEL, parse, publisher


@pytest.mark.parametrize(
    "upload_if",
    [
        "${{ env.CS_ACCESS_TOKEN != '' && github.ref == 'refs/heads/main' && false }}",
        (
            "${{ env.CS_ACCESS_TOKEN != '' && github.ref == 'refs/heads/main'"
            " && github.ref == 'refs/heads/develop' }}"
        ),
        (
            "${{ env.CS_ACCESS_TOKEN != '' && !(github.actor == 'x'"
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
        "pub-${{ github.ref }}",
        "pub-${{ github.event_name }}",
        "coverage-main-github.ref-github.event_name",
        "coverage-main-github.ref-${{ github.event_name }}",
    ],
    ids=["ref_only", "event_only", "literal_keys", "literal_ref"],
)
def test_the_group_is_keyed_on_the_evaluated_ref_and_event(group: str) -> None:
    """A group missing either evaluated key lets a dispatch displace a push."""
    concurrency = f"concurrency:\n  group: {group}\n  cancel-in-progress: false"
    findings = publisher_rules.publisher_findings(
        parse(publisher(concurrency=concurrency))
    )
    assert len(findings) == 1, findings
    assert "a dispatch can replace a pending push" in findings[0], findings


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        (
            "  coverage:\n",
            "  coverage:\n    concurrency:\n      group: upload\n",
            "a dispatch can replace a pending push",
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
