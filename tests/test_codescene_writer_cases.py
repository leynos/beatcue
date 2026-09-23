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
    ],
    ids=["merge_group", "review", "review_comment", "workflow_run"],
)
def test_every_pull_request_event_seeds_the_closure(source: str) -> None:
    """A queued merge, a review and a chained run each read as a pull request."""
    assert reader.starts_on_pull_request(parse(source)), source
