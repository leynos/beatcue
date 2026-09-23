"""Drive the publisher's condition splitter against fixtures.

Split from ``test_codescene_publisher_cases.py`` under the repository's
400-line cap. The ref-guard clause is only as good as the split beneath it, so
its quoting rules are pinned here on their own.
"""

from __future__ import annotations

import pytest
from codescene_contract import publisher_rules


@pytest.mark.parametrize(
    ("condition", "expected"),
    [
        ("${{ github.ref == 'refs/heads/main' && env.X != 'a||b' }}", 2),
        ("${{ github.ref == 'refs/heads/main' && env.X != 'a&&b' }}", 2),
        ("github.ref == 'refs/heads/main' || true", None),
    ],
    ids=["quoted_or", "quoted_and", "bare_or"],
)
def test_quoted_operators_are_not_operators(
    condition: str, expected: int | None
) -> None:
    """A ``||`` or ``&&`` inside a quoted literal is not an operator."""
    parts = publisher_rules.conjuncts(condition)
    assert (None if parts is None else len(parts)) == expected
