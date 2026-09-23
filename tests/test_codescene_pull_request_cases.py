"""Drive the CV-005 readers and pull-request rules against fixtures.

Every real workflow complies, so a rule exercised only over them passes whether
or not it detects anything. Each case builds the breach it names and asserts
the rule reports it; the compliant fixtures assert it stays quiet.
"""

from __future__ import annotations

import textwrap

import pytest
from codescene_contract import publisher_rules, reader, rules

SECRET = "${{ secrets.CS_ACCESS_TOKEN }}"  # noqa: S105 - an expression


def parse(source: str) -> object:
    """Parse a fixture through the contract's own strict reader."""
    return reader.parse("fixture", textwrap.dedent(source))


BREACHING_PULL_REQUEST = """
on:
  pull_request:
jobs:
  build:
    steps:
      - uses: leynos/shared-actions/.github/actions/generate-coverage@abc
        with:
          output-path: coverage.xml
      - env:
          CS_ACCESS_TOKEN: ${{ secrets.CS_ACCESS_TOKEN }}
        uses: leynos/shared-actions/.github/actions/upload-codescene-coverage@abc
      - run: cs-coverage upload --format cobertura
      - run: curl https://api.codescene.io/v2/projects
"""

COMPLIANT_PULL_REQUEST = """
on:
  pull_request:
jobs:
  build:
    steps:
      - uses: leynos/shared-actions/.github/actions/generate-coverage@abc
        with:
          output-path: coverage.xml
          with-ratchet: 'true'
          publish-artefact: 'false'
"""


@pytest.mark.parametrize(
    ("source", "expected"),
    [(BREACHING_PULL_REQUEST, 6), (COMPLIANT_PULL_REQUEST, 0)],
    ids=["breaching", "compliant"],
)
def test_the_pull_request_rule_reports_what_it_should(
    source: str, expected: int
) -> None:
    """Token, host, action, CLI, missing ratchet and published report are six."""
    findings = rules.pull_request_findings(parse(source))
    assert len(findings) == expected, findings


@pytest.mark.parametrize(
    "job",
    [
        f"steps:\n  - run: echo {SECRET}\n",
        f"steps:\n  - uses: x/y@abc\n    with:\n      token: {SECRET}\n",
        f"env:\n  T: {SECRET}\nsteps:\n  - run: 'true'\n",
        f"uses: ./.github/workflows/c.yml\nsecrets:\n  CS_ACCESS_TOKEN: {SECRET}\n",
        "uses: ./.github/workflows/c.yml\nsecrets: inherit\n",
        "steps:\n  - run: echo ${{ secrets[format('CS_{0}', 'ACCESS_TOKEN')] }}\n",
        "steps:\n  - run: echo '${{ toJSON(secrets) }}'\n",
        "steps:\n  - run: echo ${{ secrets.Cs_Access_Token }}\n",
        "steps:\n  - run: echo ${{ SECRETS['CS_' + 'ACCESS_TOKEN'] }}\n",
    ],
    ids=[
        "run_body",
        "action_input",
        "env_value",
        "named_forwarding",
        "inherit",
        "computed_name",
        "whole_context",
        "name_in_another_case",
        "context_in_another_case",
    ],
)
def test_every_route_to_the_token_is_reported(job: str) -> None:
    """A reference in each position, and inheritance, are each reported."""
    indented = textwrap.indent(job, "    ")
    source = f"on: pull_request\njobs:\n  lane:\n{indented}"
    assert rules.pull_request_findings(parse(source)), source


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        (
            "Leynos/Shared-Actions/.github/actions/upload-codescene-coverage@abc",
            "invokes",
        ),
        (
            "LEYNOS/shared-actions/.github/actions/generate-coverage@abc",
            "does not set with-ratchet",
        ),
    ],
    ids=["uploader", "generator"],
)
def test_an_action_is_matched_whatever_the_case(action: str, expected: str) -> None:
    """GitHub resolves the owner and repository case-insensitively."""
    source = f"on: pull_request\njobs:\n  lane:\n    steps:\n      - uses: {action}\n"
    findings = rules.pull_request_findings(parse(source))
    assert any(expected in finding for finding in findings), findings


def test_a_named_secret_and_prose_are_not_computed_references() -> None:
    """A named reference to another secret and the word in prose are clean."""
    source = (
        "on: pull_request\njobs:\n  lane:\n    steps:\n"
        "      - run: echo ${{ secrets.GITHUB_TOKEN }} keeps secrets out of logs\n"
    )
    assert not rules.pull_request_findings(parse(source))


def test_a_call_to_a_missing_workflow_is_reported() -> None:
    """A local call to an absent file is reported, not dropped in silence."""
    caller = (
        "on: pull_request\njobs:\n  call:\n    uses: ./.github/workflows/missing.yml\n"
    )
    all_workflows = {"caller.yml": parse(caller)}
    missing = reader.missing_callees(
        all_workflows, reader.pull_request_closure(all_workflows)
    )
    assert len(missing) == 1, missing
    assert "missing.yml" in missing[0]


LEAKING_CALLEE = """
on: workflow_call
jobs:
  leak:
    steps:
      - run: |
          curl -H "Authorization: ${{ secrets.CS_ACCESS_TOKEN }}" https://codescene.io/api
"""


@pytest.mark.parametrize(
    "call",
    ["./.github/workflows/called.yml", ".github/workflows/called.yml"],
    ids=["dot_prefixed", "bare"],
)
def test_a_called_workflow_is_inside_the_pull_request_closure(call: str) -> None:
    """A ``workflow_call``-only callee is in the closure, and its leak is found."""
    caller = (
        f"on: [pull_request]\njobs:\n  call:\n    uses: {call}\n    secrets: inherit\n"
    )
    all_workflows = {"caller.yml": parse(caller), "called.yml": parse(LEAKING_CALLEE)}
    assert "called.yml" in reader.pull_request_closure(all_workflows)
    findings = rules.pull_request_findings(all_workflows["called.yml"])
    assert len(findings) == 2, findings


@pytest.mark.parametrize(
    ("reference", "expected"),
    [
        ("./.github/workflows/called.yml", (reader.CallKind.LOCAL, "called.yml")),
        ("$/.github/workflows/called.yml", (reader.CallKind.LOCAL, "called.yml")),
        (
            "leynos/shared-actions/.github/workflows/called.yml@abc",
            (reader.CallKind.REMOTE, None),
        ),
        ("$/.github/workflows/called.yml@main", (reader.CallKind.REFUSED, None)),
        ("./.github/workflows/called.yml@main", (reader.CallKind.REFUSED, None)),
        ("./.github/workflows/sub/called.yml", (reader.CallKind.REFUSED, None)),
    ],
    ids=["dot", "dollar", "remote", "dollar_ref", "dot_ref", "nested"],
)
def test_each_call_spelling_is_classified(
    reference: str, expected: tuple[reader.CallKind, str | None]
) -> None:
    """``./`` and ``$/`` are local; an ``@ref`` or subdirectory is refused."""
    assert reader.classify_call(reference) == expected


def test_a_refused_call_is_a_finding() -> None:
    """The pull-request rule reports a refused call, naming the job."""
    source = (
        "on: pull_request\njobs:\n  call:\n    uses: $/.github/workflows/c.yml@main\n"
    )
    findings = rules.pull_request_findings(parse(source))
    assert len(findings) == 1, findings
    assert "resolves to no workflow" in findings[0]


def test_the_closure_follows_a_chain_of_calls() -> None:
    """A leak two calls deep is reached through a clean middle workflow."""
    all_workflows = {
        "caller.yml": parse(
            "on: pull_request\njobs:\n  first:\n"
            "    uses: ./.github/workflows/middle.yml\n"
        ),
        "middle.yml": parse(
            "on: workflow_call\njobs:\n  second:\n"
            "    uses: $/.github/workflows/leaf.yml\n"
        ),
        "leaf.yml": parse(
            "on: workflow_call\njobs:\n  leak:\n    steps:\n"
            "      - run: curl https://codescene.io/api\n"
        ),
    }
    closure = reader.pull_request_closure(all_workflows)
    assert {"middle.yml", "leaf.yml"} <= closure, closure
    assert len(rules.pull_request_findings(all_workflows["leaf.yml"])) == 1


@pytest.mark.parametrize(
    "source",
    [
        "on: pull_request\njobs: {}\n",
        "on: [push, pull_request]\njobs: {}\n",
        "on:\n  pull_request:\njobs: {}\n",
        "'on':\n  pull_request:\njobs: {}\n",
        "true:\n  pull_request:\njobs: {}\n",
        "on: [pull_request_target]\njobs: {}\n",
    ],
    ids=["scalar", "sequence", "mapping", "quoted_key", "boolean_key", "target"],
)
def test_every_trigger_form_is_read(source: str) -> None:
    """Every form GitHub accepts is read as a pull request."""
    assert reader.starts_on_pull_request(parse(source)), source


@pytest.mark.parametrize(
    ("source", "reason"),
    [
        (
            "on: pull_request\njobs:\n  a:\n    runs-on: x\n    runs-on: y\n",
            "duplicate key",
        ),
        ("'on': push\ntrue: pull_request\njobs: {}\n", "both"),
    ],
    ids=["duplicate_key", "both_trigger_keys"],
)
def test_an_ambiguous_mapping_is_refused(source: str, reason: str) -> None:
    """A repeated key, or triggers under both ``on`` and ``true``, is refused."""
    with pytest.raises(reader.WorkflowError, match=reason):
        parse(source)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            (
                "on: pull_request\ndefaults:\n  run:\n"
                "    shell: curl https://API.CodeScene.io/x; bash {0}\njobs: {}\n"
            ),
            "contacts codescene.io",
        ),
        (
            (
                "on:\n  workflow_call:\n    secrets:\n      CS_ACCESS_TOKEN:\n"
                "        required: false\njobs: {}\n"
            ),
            "receives CS_ACCESS_TOKEN",
        ),
    ],
    ids=["default_shell", "declared_secret"],
)
def test_the_whole_document_is_searched(source: str, expected: str) -> None:
    """A default shell reaching the host and a declared secret are both found."""
    findings = rules.pull_request_findings(parse(source))
    assert len(findings) == 1, findings
    assert expected in findings[0]


SECOND_WRITER = """
on:
  push:
    branches: [main]
  pull_request:
jobs:
  build:
    steps:
      - uses: leynos/shared-actions/.github/actions/generate-coverage@abc
        if: @GUARD@
        with:
          with-ratchet: 'true'
"""


@pytest.mark.parametrize(
    ("guard", "expected"),
    [
        ("github.event_name == 'pull_request'", 0),
        ("github.event_name == 'push'", 1),
        ("github.event_name == 'pull_request' || true", 1),
        ("always()", 1),
    ],
    ids=["guarded", "push_only", "disjunction", "unguarded"],
)
def test_a_pull_request_lane_on_push_cannot_write_the_baseline(
    guard: str, expected: int
) -> None:
    """A lane that also runs on push must keep its ratchet off the push."""
    source = SECOND_WRITER.replace("@GUARD@", f'"{guard}"')
    findings = publisher_rules.second_writer_findings(parse(source))
    assert len(findings) == expected, findings


def test_a_pull_request_lane_may_not_publish_its_baseline() -> None:
    """``publish-baseline: always`` on a pull-request lane is refused."""
    source = COMPLIANT_PULL_REQUEST.replace(
        "publish-artefact: 'false'",
        "publish-artefact: 'false'\n          publish-baseline: always",
    )
    findings = rules.pull_request_findings(parse(source))
    assert len(findings) == 1, findings
    assert "may publish its baseline" in findings[0]


def test_a_called_workflow_runs_with_its_callers_push() -> None:
    """A ``workflow_call`` callee inherits the push that called it."""
    source = SECOND_WRITER.replace(
        "on:\n  push:\n    branches: [main]\n  pull_request:\n", "on: workflow_call\n"
    ).replace("@GUARD@", '"always()"')
    findings = publisher_rules.second_writer_findings(parse(source))
    assert len(findings) == 1, findings


@pytest.mark.parametrize(
    ("step", "expected"),
    [
        ("      - run: echo ${{ secrets.CS_ACCESS_TOKEN }}\n", "receives"),
        ("      - run: curl -fsSL https://downloads.codescene.io/x.sh\n", "contacts"),
        (
            "      - run: gh variable set CODESCENE_CLI_SHA256 --body x\n",
            "retired installer digest",
        ),
        ("      - run: cs-coverage upload --format lcov\n", "runs cs-coverage"),
        (
            (
                "      - uses: leynos/shared-actions/.github/actions/"
                "upload-codescene-coverage@abc\n"
            ),
            "invokes",
        ),
    ],
    ids=["token", "host", "digest", "cli", "uploader"],
)
def test_a_workflow_outside_both_lanes_is_read(step: str, expected: str) -> None:
    """A tag- or dispatch-triggered workflow cannot reach CodeScene either."""
    source = f"on:\n  push:\n    tags: ['v*']\njobs:\n  job:\n    steps:\n{step}"
    findings = rules.stray_findings(parse(source))
    assert any(expected in finding for finding in findings), findings


def test_a_workflow_without_codescene_is_not_a_stray() -> None:
    """A release workflow naming no CodeScene surface has no findings."""
    source = (
        "on: workflow_dispatch\njobs:\n  job:\n    steps:\n      - run: make build\n"
    )
    assert not rules.stray_findings(parse(source))
