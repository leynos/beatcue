"""Read workflows for the CV-005 contract.

Every reader here errs towards seeing more. A workflow the contract cannot see
is a workflow it passes, so each place GitHub accepts more than one spelling is
read in all of them: both file extensions in either case, the ``on`` key as a
string or as the boolean YAML 1.1 makes of it, a trigger written as a scalar, a
sequence or a mapping, and a reusable-workflow call however its local path is
prefixed.
"""

from __future__ import annotations

import enum
import typing as typ
from pathlib import Path

import yaml

if typ.TYPE_CHECKING:
    import collections.abc as cabc

WORKFLOW_PREFIX = ".github/workflows/"
WORKFLOW_DIR = Path(__file__).resolve().parents[2] / ".github" / "workflows"
WORKFLOW_SUFFIXES = frozenset({".yml", ".yaml"})

type Mapping = dict[object, object]
type Workflows = dict[str, object]


class WorkflowError(ValueError):
    """A workflow the contract refuses to read."""


class _StrictLoader(yaml.SafeLoader):
    """A ``SafeLoader`` that refuses a mapping declaring one key twice.

    PyYAML keeps the last duplicate and says nothing, so a lane could carry one
    ``runs-on`` or ``if:`` in the file and another in the parse.
    """


def _construct_strict_mapping(
    loader: _StrictLoader, node: yaml.MappingNode
) -> dict[typ.Hashable, typ.Any]:
    """Construct a mapping, refusing a repeated key."""
    seen: set[object] = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=True)
        if key in seen:
            msg = f"duplicate key {key!r} at line {key_node.start_mark.line + 1}"
            raise WorkflowError(msg)
        seen.add(key)
    return loader.construct_mapping(node, deep=True)


_StrictLoader.add_constructor(
    yaml.SafeLoader.DEFAULT_MAPPING_TAG, _construct_strict_mapping
)


def _declares_both_trigger_keys(parsed: object) -> bool:
    """Return whether a document declares triggers under ``on`` and ``true``."""
    return isinstance(parsed, dict) and {"on", True} <= parsed.keys()


def parse(name: str, text: str) -> object:
    """Parse one workflow, refusing duplicate keys and a doubled trigger key.

    ``on`` and a bare ``true`` are different keys to the parser, yet GitHub reads
    both as the trigger block and merges them, so a reader that picks one is
    blind to the other. A workflow declaring both is refused here rather than
    read either way. This is the one place the contract parses.
    """
    try:
        parsed = yaml.load(text, Loader=_StrictLoader)  # noqa: S506 - SafeLoader subclass
    except yaml.YAMLError as error:
        msg = f"{name} is not valid YAML: {error}"
        raise WorkflowError(msg) from error
    except WorkflowError as error:
        msg = f"{name}: {error}"
        raise WorkflowError(msg) from error
    if _declares_both_trigger_keys(parsed):
        msg = f"{name} declares its triggers under both `on` and `true`"
        raise WorkflowError(msg)
    return parsed


def workflows(directory: Path = WORKFLOW_DIR) -> Workflows:
    """Read every workflow in ``directory``, keyed by file name.

    An empty or missing directory is an error, since every contract ranging
    over an empty set would pass.
    """
    found = {
        path.name: parse(path.name, path.read_text(encoding="utf-8"))
        for path in sorted(directory.iterdir())
        if path.suffix.lower() in WORKFLOW_SUFFIXES
    }
    if not found:
        msg = f"no workflows found under {directory}"
        raise WorkflowError(msg)
    return found


def as_mapping(value: object) -> Mapping | None:
    """Return ``value`` when it is a mapping."""
    return typ.cast("Mapping", value) if isinstance(value, dict) else None


def get(mapping: Mapping | None, key: str) -> object:
    """Return the value under ``key``, or ``None``."""
    return None if mapping is None else mapping.get(key)


def get_str(mapping: Mapping | None, key: str) -> str | None:
    """Return the value under ``key`` when it is a string."""
    value = get(mapping, key)
    return value if isinstance(value, str) else None


def _on_block(workflow: object) -> object:
    """Return the trigger block under either spelling of its key."""
    root = as_mapping(workflow)
    if root is None:
        return None
    return root.get("on", root.get(True))


def trigger_names(workflow: object) -> list[str]:
    """Return the event names a workflow declares, in any of the three forms.

    A mapping-only reader stringifies ``on: [push, pull_request]`` into one key
    named after the whole list, and the workflow escapes every clause.
    """
    block = _on_block(workflow)
    if isinstance(block, str):
        return [block]
    if isinstance(block, list):
        return [name for name in block if isinstance(name, str)]
    if isinstance(block, dict):
        return [name for name in block if isinstance(name, str)]
    return []


def trigger(workflow: object, event: str) -> object:
    """Return one trigger's configuration, when written as a mapping."""
    return get(as_mapping(_on_block(workflow)), event)


# Events that start a workflow for a pull request, or straight after one.
# Besides the two `pull_request` events, a queued merge and a review run with
# the repository's secrets for a same-repository pull request, and a
# `workflow_run` workflow runs with secrets after whatever it names, which may
# be a pull-request workflow.
PULL_REQUEST_EVENTS = frozenset({
    "merge_group",
    "pull_request",
    "pull_request_review",
    "pull_request_review_comment",
    "pull_request_target",
    "workflow_run",
})


def starts_on_pull_request(workflow: object) -> bool:
    """Return whether an event run for a pull request starts the workflow."""
    return any(name in PULL_REQUEST_EVENTS for name in trigger_names(workflow))


def jobs(workflow: object) -> list[tuple[str, Mapping]]:
    """Return every job of a workflow as ``(job id, job mapping)``."""
    block = as_mapping(get(as_mapping(workflow), "jobs"))
    if block is None:
        return []
    return [
        (job_id, job)
        for job_id, value in block.items()
        if isinstance(job_id, str) and (job := as_mapping(value)) is not None
    ]


def job_steps(job: Mapping) -> list[Mapping]:
    """Return every step of one job."""
    listed = get(job, "steps")
    if not isinstance(listed, list):
        return []
    return [step for item in listed if (step := as_mapping(item)) is not None]


def steps(workflow: object) -> list[Mapping]:
    """Return every step of every job in a workflow."""
    return [step for _, job in jobs(workflow) for step in job_steps(job)]


def uses(step: Mapping) -> str | None:
    """Return a step's ``uses`` reference, when it has one."""
    return get_str(step, "uses")


class CallKind(enum.Enum):
    """What a job-level ``uses:`` reference names."""

    LOCAL = "local"
    REFUSED = "refused"
    REMOTE = "remote"


def classify_call(reference: str) -> tuple[CallKind, str | None]:
    """Classify a job-level ``uses`` reference, with the local file it names.

    Matched by shape rather than by an enumerated list of spellings: a leading
    ``./`` or GitHub's documented ``$/`` is stripped, and what remains is local
    when it is a path under ``.github/workflows/``. A local-shaped reference
    carrying an ``@ref`` or naming a subdirectory is refused rather than read as
    remote: it resolves to no file here, and what it runs would escape.
    """
    path = reference.removeprefix("./")
    if path == reference:
        path = reference.removeprefix("$/")
    if not path.startswith(WORKFLOW_PREFIX):
        return CallKind.REMOTE, None
    file = path.removeprefix(WORKFLOW_PREFIX)
    if not file or any(character in file for character in "/@"):
        return CallKind.REFUSED, None
    return CallKind.LOCAL, file


def job_calls(workflow: object) -> list[tuple[str, str]]:
    """Return each job's ``uses`` reference, with the job's id."""
    return [
        (job_id, reference)
        for job_id, job in jobs(workflow)
        if (reference := get_str(job, "uses")) is not None
    ]


def _local_callees(workflow: object) -> cabc.Iterator[str]:
    """Yield each local workflow file a workflow's jobs call."""
    for _, reference in job_calls(workflow):
        kind, file = classify_call(reference)
        if kind is CallKind.LOCAL and file is not None:
            yield file


def pull_request_closure(all_workflows: Workflows) -> set[str]:
    """Return the workflows a pull request can reach, by file name.

    This starts from every workflow a pull request triggers and follows local
    job-level calls until nothing new is reached. A ``workflow_call``-only
    workflow never names a pull request, yet runs with whatever its caller
    hands it, including every secret under ``secrets: inherit``.
    """
    return closure_from(
        all_workflows,
        {
            name
            for name, workflow in all_workflows.items()
            if starts_on_pull_request(workflow)
        },
    )


def closure_from(all_workflows: Workflows, seeds: set[str]) -> set[str]:
    """Return ``seeds`` and every local workflow they reach through job calls.

    A called workflow runs with its caller's event and secrets, so whatever a
    seed may do on its trigger, its callees may do too.
    """
    reached = set(seeds)
    pending = list(reached)
    while pending:
        for callee in _local_callees(all_workflows.get(pending.pop())):
            if callee in all_workflows and callee not in reached:
                reached.add(callee)
                pending.append(callee)
    return reached


def missing_callees(all_workflows: Workflows, names: set[str]) -> list[str]:
    """Return each local call, from the named workflows, to an absent file.

    The closure can follow only a file it has read, so a call to a missing file
    would otherwise drop out of it in silence.
    """
    return [
        f"{name} calls `{callee}`, which is not there"
        for name in sorted(names)
        for callee in _local_callees(all_workflows.get(name))
        if callee not in all_workflows
    ]
