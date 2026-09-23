"""The CV-005 token check step the publisher's upload is guarded on.

Split from ``publisher_rules.py`` under the repository's 400-line cap. The
upload action is composite and hands a step ``env`` to its nested steps, so no
step holds the token in its ``env``: a check step reports whether it is set.
"""

from __future__ import annotations

from codescene_contract import reader

# The token check step's one command, exactly. The expression evaluates to
# `true` or `false` before the shell runs, so there is no shell conditional and
# the step binds nothing: no step holds the token in its `env`.
CHECK_COMMAND = (
    'echo "available=${{ secrets.CS_ACCESS_TOKEN != \'\' }}" >> "$GITHUB_OUTPUT"'
)


def check_steps(workflow: object) -> list[reader.Mapping]:
    """Return the steps that run ``CHECK_COMMAND``, and nothing else."""
    return [
        step
        for step in reader.steps(workflow)
        if (reader.get_str(step, "run") or "").strip() == CHECK_COMMAND
    ]


def check_id(workflow: object) -> str | None:
    """Return the token check step's id, when there is exactly one such step."""
    checks = check_steps(workflow)
    return reader.get_str(checks[0], "id") if len(checks) == 1 else None


def check_findings(workflow: object) -> list[str]:
    """Return the reasons the token check step is missing or cannot be trusted.

    The check must exist exactly once (deleted, the upload skips forever),
    carry an id the upload can read, and run with no ``if:``.
    """
    checks = check_steps(workflow)
    if len(checks) != 1:
        return [
            (
                "the publisher needs exactly one token check step running "
                f"`{CHECK_COMMAND}`, found {len(checks)}"
            )
        ]
    check = checks[0]
    return [
        f"the token check step {reason}"
        for is_broken, reason in (
            (reader.get_str(check, "id") is None, "has no id"),
            (reader.get(check, "if") is not None, "carries an `if:`"),
        )
        if is_broken
    ]
