"""The CV-005 token check step the publisher's upload is guarded on.

Split from ``publisher_rules.py`` under the repository's 400-line cap. The
upload action is composite and hands a step ``env`` to its nested steps, so no
step holds the token in its ``env``: a check step reports whether it is set.
"""

from __future__ import annotations

from codescene_contract import reader
from codescene_contract.rules import is_upload

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


# The keys the token check step may declare, besides its absent `if:`. Anything
# else can stop it answering while it still reads as present: a `shell` of
# `bash -c 'exit 0; {0}'` runs nothing, and `continue-on-error` lets a failed
# write pass, so the upload skips forever either way.
CHECK_STEP_KEYS = frozenset({"id", "name", "run"})


def _check_precedes_every_upload(workflow: object, check: reader.Mapping) -> bool:
    """Return whether every upload runs after the token check, in its job.

    A ``steps.<id>`` context resolves only in the job that ran the step, and
    only once it has run, so a check in another job or after the upload leaves
    the answer empty and the upload skipped on every push.
    """
    for _, job in reader.jobs(workflow):
        job_steps = reader.job_steps(job)
        uploads = [at for at, step in enumerate(job_steps) if is_upload(step)]
        if not uploads:
            continue
        check_at = next(
            (at for at, step in enumerate(job_steps) if step is check), None
        )
        if check_at is None or check_at >= min(uploads):
            return False
    return True


def check_findings(workflow: object) -> list[str]:
    """Return the reasons the token check step is missing or cannot be trusted.

    The check must exist exactly once (deleted, the upload skips forever),
    carry an id the upload can read, run with no ``if:``, come before every
    upload in the upload's own job, and declare nothing beyond
    ``CHECK_STEP_KEYS``.
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
    extra_keys = [
        f"the token check step declares `{key}`"
        for key in check
        if key != "if" and key not in CHECK_STEP_KEYS
    ]
    return [
        f"the token check step {reason}"
        for is_broken, reason in (
            (reader.get_str(check, "id") is None, "has no id"),
            (reader.get(check, "if") is not None, "carries an `if:`"),
            (
                not _check_precedes_every_upload(workflow, check),
                "does not run before every upload in the upload's job",
            ),
        )
        if is_broken
    ] + extra_keys
