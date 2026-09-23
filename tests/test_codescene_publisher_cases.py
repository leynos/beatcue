"""Drive the CV-005 main-publisher rules against fixtures.

Each case varies one clause of an otherwise complying publisher and asserts the
rule names that clause and nothing else.
"""

from __future__ import annotations

import textwrap

import pytest
from codescene_contract import publisher_rules, reader


def parse(source: str) -> object:
    """Parse a fixture through the contract's own strict reader."""
    return reader.parse("fixture", textwrap.dedent(source))


def test_a_push_restricted_to_main_is_the_publisher() -> None:
    """A push filtered to ``main`` alone makes a workflow the publisher."""
    source = "on:\n  push:\n    branches: [main]\njobs: {}\n"
    assert publisher_rules.publishes_from_main(parse(source))


@pytest.mark.parametrize(
    "source",
    [
        "on:\n  push:\njobs: {}\n",
        "on: push\njobs: {}\n",
        "on:\n  push:\n    tags: ['v*']\njobs: {}\n",
        "on:\n  push:\n    branches: [develop]\njobs: {}\n",
        "on:\n  push:\n    branches: [main, develop]\njobs: {}\n",
    ],
    ids=["unfiltered", "scalar", "tags", "another", "main_and_another"],
)
def test_any_other_push_is_not_the_publisher(source: str) -> None:
    """A push on every branch, on tags, or on another branch is not ``main``'s."""
    assert not publisher_rules.publishes_from_main(parse(source))


PUBLISHER = """
on:
  push:
    branches: [main]
  workflow_dispatch:
@CONCURRENCY@
jobs:
  coverage:
    steps:
      - uses: leynos/shared-actions/.github/actions/generate-coverage@abc
        with:
          with-ratchet: 'true'
@EXTRA_STEP@
      - env:
          CS_ACCESS_TOKEN: ${{ secrets.CS_ACCESS_TOKEN }}
        if: "@UPLOAD_IF@"
        uses: leynos/shared-actions/.github/actions/upload-codescene-coverage@abc
        with:
          access-token: ${{ env.CS_ACCESS_TOKEN }}
"""
NEVER_CANCEL = (
    "concurrency:\n  group: pub-${{ github.ref }}-${{ github.event_name }}\n"
    "  cancel-in-progress: false"
)
GUARD = "${{ env.CS_ACCESS_TOKEN != '' && github.ref == 'refs/heads/main' }}"


def publisher(
    concurrency: str = NEVER_CANCEL, upload_if: str = GUARD, extra_step: str = ""
) -> str:
    """Render ``PUBLISHER`` with the pieces a case varies."""
    return (
        PUBLISHER
        .replace("@CONCURRENCY@", concurrency)
        .replace("@UPLOAD_IF@", upload_if)
        .replace("@EXTRA_STEP@", extra_step)
    )


def assert_one_finding(findings: list[str], clause: str | None) -> None:
    """Assert ``findings`` is empty, or is one finding naming ``clause``."""
    if clause is None:
        assert not findings, findings
    else:
        assert len(findings) == 1, findings
        assert clause in findings[0], findings


@pytest.mark.parametrize(
    ("concurrency", "upload_if", "expected"),
    [
        (NEVER_CANCEL, GUARD, None),
        (
            NEVER_CANCEL,
            (
                "${{ env.CS_ACCESS_TOKEN != '' && github.ref == 'refs/heads/main'"
                " || github.event_name == 'workflow_dispatch' }}"
            ),
            "not guarded",
        ),
        (
            NEVER_CANCEL,
            (
                "${{ github.event_name == 'workflow_dispatch'"
                " || env.CS_ACCESS_TOKEN != '' && github.ref == 'refs/heads/main' }}"
            ),
            "not guarded",
        ),
        (
            NEVER_CANCEL,
            (
                "${{ env.CS_ACCESS_TOKEN != '' && github.ref == 'refs/heads/main'"
                " && github.actor != 'x' || github.event_name == 'workflow_dispatch' }}"
            ),
            "not guarded",
        ),
        (
            NEVER_CANCEL,
            (
                "${{ env.CS_ACCESS_TOKEN != '' && github.ref == 'refs/heads/main'"
                " && github.actor != 'x' }}"
            ),
            "not guarded",
        ),
        (NEVER_CANCEL, "${{ env.CS_ACCESS_TOKEN != '' }}", "not guarded"),
        (NEVER_CANCEL.replace("false", "true"), GUARD, "cancel"),
        (
            NEVER_CANCEL.replace("false", "${{ true }}"),
            GUARD,
            "cancel",
        ),
        ("", GUARD, "no concurrency group"),
        (
            "concurrency:\n  group: pub\n  cancel-in-progress: false",
            GUARD,
            "a dispatch can replace a pending push",
        ),
    ],
    ids=[
        "complies",
        "disjunction_appended",
        "disjunction_prepended",
        "disjunction_in_extra_conjunct",
        "narrowing_conjunct",
        "no_ref_guard",
        "cancels",
        "cancels_by_expression",
        "no_group",
        "dispatches_share_the_group",
    ],
)
def test_the_publisher_rule_names_the_clause_broken(
    concurrency: str, upload_if: str, expected: str | None
) -> None:
    """Each variation is reported by the clause it breaks.

    The upload guard must be exactly the token and ref conjuncts, so every
    disjunction fails the set comparison whether or not ``||`` is refused: the
    refusal is defence in depth here, proved on the splitter's own cases. An
    extra conjunct fails too; ``test_codescene_guard_cases.py`` holds the ones
    that silently stop the upload.
    """
    source = publisher(concurrency, upload_if)
    assert_one_finding(publisher_rules.publisher_findings(parse(source)), expected)


SECRET = "${{ secrets.CS_ACCESS_TOKEN }}"  # noqa: S105 - an expression
UPLOAD_TOKEN = f"      - env:\n          CS_ACCESS_TOKEN: {SECRET}\n"
WIDE_TOKEN = f"env:\n  CS_ACCESS_TOKEN: {SECRET}\n"
REUSABLE = "  forward:\n    uses: ./.github/workflows/elsewhere.yml\n"
RATCHET = "        with:\n          with-ratchet"


@pytest.mark.parametrize(
    ("replacements", "expected"),
    [
        (
            [
                (UPLOAD_TOKEN, "      - env: {}\n"),
                (
                    RATCHET,
                    f"        env:\n          CS_ACCESS_TOKEN: {SECRET}\n" + RATCHET,
                ),
            ],
            ["does not bind", "other than the upload"],
        ),
        ([("jobs:\n", WIDE_TOKEN + "jobs:\n")], ["for every job"]),
        (
            [("    steps:\n", textwrap.indent(WIDE_TOKEN, "    ") + "    steps:\n")],
            ["for every step"],
        ),
        (
            [
                (
                    "jobs:\n",
                    "jobs:\n"
                    + REUSABLE
                    + "    with:\n      token: ${{ secrets.CS_ACCESS_TOKEN }}\n",
                )
            ],
            ["to a reusable workflow"],
        ),
        (
            [
                (
                    "jobs:\n",
                    "jobs:\n"
                    + REUSABLE
                    + f"    secrets:\n      CS_ACCESS_TOKEN: {SECRET}\n",
                )
            ],
            ["to a reusable workflow"],
        ),
        (
            [("jobs:\n", "jobs:\n" + REUSABLE + "    secrets: inherit\n")],
            ["to a reusable workflow"],
        ),
        ([(UPLOAD_TOKEN, "      - env: {}\n")], ["does not bind"]),
        (
            [
                (UPLOAD_TOKEN, "      - env: {}\n"),
                (
                    "access-token: ${{ env.CS_ACCESS_TOKEN }}",
                    "access-token: ${{ secrets.CS_ACCESS_TOKEN }}",
                ),
            ],
            ["does not bind"],
        ),
        (
            [
                (
                    UPLOAD_TOKEN,
                    f"      - env:\n          CS_TOKEN: {SECRET}\n",
                )
            ],
            ["does not bind"],
        ),
        (
            [
                (
                    RATCHET,
                    "        env:\n          T: ${{ secrets['CS_ACCESS_TOKEN'] }}\n"
                    + RATCHET,
                )
            ],
            ["computed name"],
        ),
        (
            [
                (
                    RATCHET,
                    "        env:\n          T: ${{ secrets.Cs_Access_Token }}\n"
                    + RATCHET,
                )
            ],
            ["other than the upload"],
        ),
    ],
    ids=[
        "moved_to_coverage",
        "workflow_env",
        "job_env",
        "forwarded_as_an_input",
        "forwarded_by_name",
        "forwarded_by_inheritance",
        "binding_deleted",
        "binding_moved_to_the_input",
        "binding_renamed",
        "computed_elsewhere",
        "held_elsewhere_in_another_case",
    ],
)
def test_the_token_sits_on_the_upload_alone(
    replacements: list[tuple[str, str]], expected: list[str]
) -> None:
    """Each placement off the upload step's own binding is named.

    The guard ``env.CS_ACCESS_TOKEN != ''`` reads a missing binding as empty
    and skips the upload forever, so the binding is asserted, not inferred.
    """
    source = publisher()
    for old, new in replacements:
        assert source.count(old) == 1, old
        source = source.replace(old, new)
    findings = publisher_rules.publisher_findings(parse(source))
    assert len(findings) == len(expected), findings
    assert all(any(clause in f for f in findings) for clause in expected), findings


@pytest.mark.parametrize(
    "extra",
    [
        "      - run: cs-coverage upload --format cobertura\n",
        (
            "      - run: |\n          cs-coverage \\\n"
            "            upload --format cobertura\n"
        ),
        "      - run: false && cs-coverage upload --format cobertura\n",
    ],
    ids=["plain", "continued", "neutralized"],
)
def test_the_cli_is_refused_in_the_publisher(extra: str) -> None:
    """An upload is read only from the action, never from a ``run`` body."""
    findings = publisher_rules.publisher_findings(parse(publisher(extra_step=extra)))
    assert_one_finding(findings, "runs cs-coverage directly")


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        (
            RATCHET,
            "        if: github.actor == 'x'\n" + RATCHET,
            "no ratcheted coverage",
        ),
        ("  coverage:\n", "  coverage:\n    if: false\n", "carries an `if:`"),
    ],
    ids=["coverage_step_if", "job_if"],
)
def test_conditional_required_work_is_refused(
    old: str, new: str, expected: str
) -> None:
    """A condition on the job or the ratcheted coverage step can stop it."""
    source = publisher()
    assert source.count(old) == 1, old
    findings = publisher_rules.publisher_findings(parse(source.replace(old, new)))
    assert_one_finding(findings, expected)


def test_check_mode_is_not_an_upload() -> None:
    """The upload action in ``check`` mode publishes nothing."""
    source = publisher().replace(
        "          access-token:", "          mode: check\n          access-token:"
    )
    findings = publisher_rules.publisher_findings(parse(source))
    assert any("uploads nothing" in f for f in findings), findings


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
      - env:
          CS_ACCESS_TOKEN: ${{ secrets.CS_ACCESS_TOKEN }}
        uses: leynos/shared-actions/.github/actions/upload-codescene-coverage@abc
        with:
          path: coverage.xml
          format: cobertura
          access-token: ${{ env.CS_ACCESS_TOKEN }}
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
        ("          access-token: ${{ env.CS_ACCESS_TOKEN }}\n", "", "its step binds"),
        ("${{ env.CS_ACCESS_TOKEN }}", "${{ env.OTHER }}", "its step binds"),
        (
            "${{ env.CS_ACCESS_TOKEN }}",
            "${{ secrets.CS_ACCESS_TOKEN }}",
            "its step binds",
        ),
    ],
    ids=["wired", "other_path", "other_format", "no_token", "other_token", "secret"],
)
def test_the_upload_sends_what_was_measured(
    old: str, new: str, expected: str | None
) -> None:
    """The upload reads what was written and passes the token its step binds."""
    source = WIRED
    if old:
        assert WIRED.count(old) == 1, old
        source = WIRED.replace(old, new)
    assert_one_finding(publisher_rules.wiring_findings(parse(source)), expected)
