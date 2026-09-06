"""Tests that CI installs no tool without a version pin.

An unpinned linter is what turned `main` red on 2026-07-30 and kept it red:
`uv tool install ty` and `uv tool install ruff` silently followed upstream, and
the first release with a new rule failed a gate nobody had changed. Reviewing
the workflow by eye does not catch the next one, so the pin is a contract.

The assertions match the install commands themselves, not a comment or a name
near them, and each is mutation-tested by
`test_the_contract_rejects_an_unpinned_install`.
"""

from __future__ import annotations

import re
import typing as typ
from pathlib import Path

import pytest

if typ.TYPE_CHECKING:
    import collections.abc as cabc

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"

# `uv tool install X`, `uv pip install X`, `npm install -g X`. The captured
# group is everything after the subcommand on that line, quotes included.
INSTALL_COMMANDS = (
    re.compile(r"\buv tool install\s+(?P<arguments>.+)$", re.MULTILINE),
    re.compile(r"\buv pip install\s+(?P<arguments>.+)$", re.MULTILINE),
    re.compile(r"\bnpm install -g\s+(?P<arguments>.+)$", re.MULTILINE),
)

# A pinned argument is `name==version`, `name@version` or a shell expansion of
# a variable holding one of those. A bare name is not pinned.
PINNED = re.compile(r"^[A-Za-z0-9._-]+(==|@)\S+$")
LINE_CONTINUATION = re.compile(r"\\\s*$")


def _installed_arguments(text: str) -> cabc.Iterator[tuple[str, str]]:
    """Yield every (command, package argument) pair in the workflow text."""
    for pattern in INSTALL_COMMANDS:
        for match in pattern.finditer(text):
            arguments = match.group("arguments")
            for token in _package_tokens(text, match.end(), arguments):
                yield match.group(0).strip(), token


def _package_tokens(text: str, line_end: int, arguments: str) -> cabc.Iterator[str]:
    """Yield the package arguments of one install command.

    A command may continue over several lines with a trailing backslash, so the
    following lines are consumed until one does not continue.
    """
    remainder = arguments
    position = line_end
    while True:
        continues = bool(LINE_CONTINUATION.search(remainder))
        for token in remainder.rstrip("\\").split():
            if token.startswith("-"):
                continue
            yield token.strip("\"'")
        if not continues:
            return
        newline = text.find("\n", position + 1)
        if newline == -1:
            return
        remainder = text[position + 1 : newline]
        position = newline


def test_the_workflow_installs_at_least_one_tool() -> None:
    """Guard the contract itself: a pattern that matches nothing proves nothing."""
    assert list(_installed_arguments(WORKFLOW.read_text(encoding="utf-8")))


@pytest.mark.parametrize(
    ("command", "package"),
    list(_installed_arguments(WORKFLOW.read_text(encoding="utf-8"))),
    ids=lambda value: value.replace(" ", "-"),
)
def test_every_installed_tool_is_version_pinned(command: str, package: str) -> None:
    """Every package CI installs names an exact version."""
    resolved = _resolve_shell_variables(package)
    assert PINNED.match(resolved), f"{command!r} installs {package!r} without a pin"


def _resolve_shell_variables(package: str) -> str:
    """Substitute `${VAR}` with a stand-in so the pin shape can be matched."""
    return re.sub(r"\$\{[A-Za-z_][A-Za-z0-9_]*\}", "0.0.0", package)


def test_the_contract_rejects_an_unpinned_install() -> None:
    """Mutation check: dropping a pin from the workflow text must fail.

    Without this, a regex that quietly matched nothing would let every
    parametrised case pass vacuously.
    """
    mutated = 'run: |\n  uv tool install "mbake"\n'
    packages = [package for _, package in _installed_arguments(mutated)]

    assert packages == ["mbake"]
    assert not PINNED.match(_resolve_shell_variables(packages[0]))
