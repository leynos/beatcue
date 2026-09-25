"""Drive the publisher's upload wiring against fixtures.

Split from ``test_codescene_publisher_cases.py`` under the repository's
400-line cap. The upload must read what the coverage step writes and pass the
secret itself as its token.
"""

from __future__ import annotations

import pytest
from codescene_contract import publisher_rules
from test_codescene_publisher_cases import assert_one_finding, parse

WIRED = """
on:
  push:
    branches: [main]
jobs:
  coverage:
    steps:
      - uses: leynos/shared-actions/.github/actions/generate-coverage@abc
        with:
          output-path: coverage.xml
          format: cobertura
      - uses: leynos/shared-actions/.github/actions/upload-codescene-coverage@abc
        with:
          path: coverage.xml
          format: cobertura
          access-token: ${{ secrets.CS_ACCESS_TOKEN }}
"""


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ("", "", None),
        (
            "          path: coverage.xml",
            "          path: other.xml",
            "which no coverage step writes",
        ),
        (
            "          format: cobertura\n          access",
            "          format: lcov\n          access",
            "which no coverage step writes",
        ),
        (
            "          access-token: ${{ secrets.CS_ACCESS_TOKEN }}\n",
            "",
            "the secret itself",
        ),
        ("${{ secrets.CS_ACCESS_TOKEN }}", "${{ secrets.OTHER }}", "the secret itself"),
        (
            "${{ secrets.CS_ACCESS_TOKEN }}",
            "${{ env.CS_ACCESS_TOKEN }}",
            "the secret itself",
        ),
    ],
    ids=[
        "wired",
        "other_path",
        "other_format",
        "no_token",
        "other_token",
        "through_env",
    ],
)
def test_the_upload_sends_what_was_measured(
    old: str, new: str, expected: str | None
) -> None:
    """The upload reads what was written and passes the secret itself."""
    source = WIRED
    if old:
        assert WIRED.count(old) == 1, old
        source = WIRED.replace(old, new)
    assert_one_finding(publisher_rules.wiring_findings(parse(source)), expected)
