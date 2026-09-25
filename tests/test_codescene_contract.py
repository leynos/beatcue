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
        for finding in rules.pull_request_findings(all_workflows[name])
    ]
    breaches.extend(reader.missing_callees(all_workflows, closure))
    assert not breaches, breaches


def test_only_the_publisher_writes_the_baseline() -> None:
    """Scenario: every workflow a push starts, and every one it calls.

    Invariant: outside the publisher, none can run a ratcheted coverage step on
    a push. A callee runs with its caller's event, so the push side is followed
    as a closure too.
    """
    writers = publisher_rules.second_writers(reader.workflows())
    assert not writers, writers


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


def test_only_the_publisher_reaches_codescene() -> None:
    """Scenario: every workflow other than the publisher is examined.

    Invariant: none holds the token, names the host, runs the CLI or the
    uploader, or touches the retired installer digest. The pull-request and
    publisher clauses between them leave a dispatch-only or tag-triggered
    workflow unread; this one reads every file.
    """
    all_workflows = reader.workflows()
    publishers = set(_publishers(all_workflows))
    others = sorted(set(all_workflows) - publishers)
    assert others, "no workflow besides the publisher was read"
    breaches = [
        f"{name}: {finding}"
        for name in others
        for finding in rules.stray_findings(all_workflows[name])
    ]
    assert not breaches, breaches


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


# The coverage selection the publisher and every pull-request lane run, pinned
# as this repository's own value: "each lane equals the publisher" passes when
# both change together. `publish-artefact` is lane-local and left out.
COVERAGE_SELECTION = {
    "language": "python",
    "python-source": "./beatcue",
    "output-path": "coverage.xml",
    "format": "cobertura",
    "pytest-workers": "",
    "with-ratchet": "true",
}


def _selection(step: dict[object, object]) -> tuple[dict[str, str], object]:
    """Return a coverage step's inputs, less the lane-local ones, and its env."""
    inputs = reader.as_mapping(step.get("with")) or {}
    return (
        {
            str(key): str(value).strip()
            for key, value in inputs.items()
            if key != "publish-artefact"
        },
        step.get("env"),
    )


def test_the_coverage_selection_is_pinned() -> None:
    """Scenario: the publisher and each lane's coverage steps are compared.

    Invariant: the publisher measures exactly ``COVERAGE_SELECTION`` and every
    lane measures what the publisher does, with the same step environment.
    """
    all_workflows = reader.workflows()
    published = [
        _selection(step)
        for name in _publishers(all_workflows)
        for step in reader.steps(all_workflows[name])
        if rules.is_coverage(step)
    ]
    assert len(published) == 1, published
    inputs, env = published[0]
    assert inputs == COVERAGE_SELECTION, inputs
    for name in sorted(reader.pull_request_closure(all_workflows)):
        for step in reader.steps(all_workflows[name]):
            if rules.is_coverage(step):
                assert _selection(step) == (inputs, env), (name, _selection(step))
