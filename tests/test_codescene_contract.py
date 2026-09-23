"""Hold CodeScene coverage publication on ``main``, per concordat's CV-005.

The rule has three clauses, and this file asserts each against the real
workflows:

1. no workflow a pull request can reach invokes a CodeScene action, runs
   ``cs-coverage``, contacts ``codescene.io``, receives ``CS_ACCESS_TOKEN``,
   forwards every secret with ``secrets: inherit``, or publishes its coverage
   report;
2. every ``generate-coverage`` step such a workflow runs sets ``with-ratchet``,
   reads the baseline the publisher writes, and cannot write it on a push;
3. exactly one workflow outside that closure, triggered by a push restricted to
   ``main``, generates ratcheted coverage and uploads it through the shared
   action, from the one step binding the token, behind a
   ``github.ref == 'refs/heads/main'`` conjunct, in a concurrency group that
   never cancels a run in progress.

A pull request from a fork cannot read ``secrets.CS_ACCESS_TOKEN``, so an upload
on the pull-request lane is silently inert for exactly the changes that most
need reviewing, and CodeScene accepts an upload only for a branch it analyses,
which a pull request head is not. Both failures are quiet; the data simply
never arrives. "A workflow a pull request can reach" is a closure through local
reusable-workflow calls, not a trigger list. The rules are driven against
breaching fixtures in the sibling ``test_codescene_*_cases.py`` files.
"""

from __future__ import annotations

from codescene_contract import publisher_rules, reader, rules

# The floor the closure must still reach: a closure that silently emptied would
# make the first clause pass having read nothing.
KNOWN_PULL_REQUEST_WORKFLOWS = frozenset({"ci.yml"})


def _publishers(all_workflows: reader.Workflows) -> list[str]:
    """Return the push-to-main workflows no pull request can reach."""
    closure = reader.pull_request_closure(all_workflows)
    return sorted(
        name
        for name, workflow in all_workflows.items()
        if publisher_rules.publishes_from_main(workflow) and name not in closure
    )


def _baselines(workflow: object) -> list[tuple[str, str]]:
    """Return the baseline files every coverage step in ``workflow`` reads."""
    return [
        (
            rules.input_str(step, "baseline-rust-file") or "<default>",
            rules.input_str(step, "baseline-python-file") or "<default>",
        )
        for step in reader.steps(workflow)
        if rules.is_coverage(step)
    ]


def test_no_workflow_a_pull_request_reaches_touches_codescene() -> None:
    """Scenario: every workflow a pull request can reach is examined.

    Invariant: none reaches CodeScene or publishes its report, none can write
    the baseline on a push, and the closure still holds the known lanes.
    """
    all_workflows = reader.workflows()
    closure = reader.pull_request_closure(all_workflows)
    assert closure >= KNOWN_PULL_REQUEST_WORKFLOWS, closure
    breaches = [
        f"{name}: {finding}"
        for name in sorted(closure)
        for finding in (
            *rules.pull_request_findings(all_workflows[name]),
            *publisher_rules.second_writer_findings(all_workflows[name]),
        )
    ]
    breaches.extend(reader.missing_callees(all_workflows, closure))
    assert not breaches, breaches


def test_exactly_one_main_publisher_uploads_ratcheted_coverage() -> None:
    """Scenario: the repository is asked what publishes coverage.

    Invariant: exactly one push-to-main workflow outside the closure publishes,
    as clause 3 requires. Without this, the first clause is satisfied by
    deleting the upload altogether.
    """
    all_workflows = reader.workflows()
    publishers = _publishers(all_workflows)
    assert len(publishers) == 1, publishers
    workflow = all_workflows[publishers[0]]
    findings = [
        *publisher_rules.publisher_findings(workflow),
        *publisher_rules.wiring_findings(workflow),
    ]
    assert not findings, findings


def test_every_pull_request_lane_reads_the_publisher_baseline() -> None:
    """Scenario: the publisher and each pull-request lane are compared.

    Invariant: every lane reads the baseline the publisher writes, judged per
    lane so one lane that agrees cannot cover for another.
    """
    all_workflows = reader.workflows()
    written = [
        baseline
        for name in _publishers(all_workflows)
        for baseline in _baselines(all_workflows[name])
    ]
    assert len(written) == 1, written
    lanes = {
        name: _baselines(all_workflows[name])
        for name in reader.pull_request_closure(all_workflows)
    }
    assert any(lanes.values()), "no pull-request lane measures coverage"
    for name, read in lanes.items():
        assert all(baseline == written[0] for baseline in read), (name, read, written)
