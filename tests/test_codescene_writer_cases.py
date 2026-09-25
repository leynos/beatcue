"""Drive the push-side closure and the pull-request seed events.

Split from ``test_codescene_pull_request_cases.py`` under the repository's
400-line cap. Both are about which workflows a clause must read: every lane a
push can start must stay off the baseline, and every event that runs a
workflow for a pull request must seed the pull-request closure.
"""

from __future__ import annotations

import textwrap

import pytest
from codescene_contract import publisher_rules, reader

CALLER = """
on:
  push:
    branches: ['**']
jobs:
  call:
    uses: ./.github/workflows/cov.yml
"""
CALLEE = """
on: workflow_call
jobs:
  cov:
    steps:
      - uses: leynos/shared-actions/.github/actions/generate-coverage@abc
        with:
          with-ratchet: 'true'
"""


def parse(source: str) -> object:
    """Parse a fixture through the contract's own strict reader."""
    return reader.parse("fixture", textwrap.dedent(source))


def test_a_callee_of_a_push_lane_is_a_second_writer() -> None:
    """The query the real-file test runs reaches the callee and reports it."""
    writers = publisher_rules.second_writers({
        "caller.yml": parse(CALLER),
        "cov.yml": parse(CALLEE),
    })
    assert len(writers) == 1, writers
    assert writers[0].startswith("cov.yml"), writers


@pytest.mark.parametrize(
    "source",
    [
        "on: merge_group\njobs: {}\n",
        "on:\n  pull_request_review:\n    types: [submitted]\njobs: {}\n",
        "on: [pull_request_review_comment]\njobs: {}\n",
        "on:\n  workflow_run:\n    workflows: [CI]\njobs: {}\n",
        "on: issue_comment\njobs: {}\n",
        "on: push\njobs: {}\n",
        "on:\n  push:\n    branches: ['**']\njobs: {}\n",
        "on:\n  push:\n    branches-ignore: [gh-pages]\njobs: {}\n",
        "on:\n  push:\n    branches: [main, 'feature/*']\njobs: {}\n",
    ],
    ids=[
        "merge_group",
        "review",
        "review_comment",
        "workflow_run",
        "issue_comment",
        "push_every_branch",
        "push_glob",
        "push_ignoring",
        "push_main_and_more",
    ],
)
def test_every_pull_request_event_seeds_the_closure(source: str) -> None:
    """A queued merge, a review and a chained run each read as a pull request."""
    assert reader.starts_on_pull_request(parse(source)), source


@pytest.mark.parametrize(
    "source",
    [
        "on:\n  push:\n    branches: [main]\njobs: {}\n",
        "on:\n  push:\n    tags: ['v*']\njobs: {}\n",
        "on:\n  schedule:\n    - cron: '0 0 * * *'\njobs: {}\n",
    ],
    ids=["push_main", "push_tags", "schedule"],
)
def test_trunk_tag_and_scheduled_runs_stay_off_the_surface(source: str) -> None:
    """A trunk push, a tag push and a schedule do not seed the surface.

    The seed rule is narrow: reading every push as a pull request would put
    the publisher itself on the surface.
    """
    assert not reader.starts_on_pull_request(parse(source)), source


def test_a_negated_pull_request_guard_is_not_a_guard() -> None:
    """A negated group carrying the guard runs the step on a push."""
    source = CALLEE.replace(
        "on: workflow_call\n", "on:\n  push:\n    branches: [main]\n"
    ).replace(
        "      - uses:",
        "      - if: \"!(github.actor == 'x'"
        " && github.event_name == 'pull_request')\"\n"
        "        uses:",
    )
    assert len(publisher_rules.second_writer_findings(parse(source))) == 1
