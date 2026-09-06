"""Tests that CI installs nothing without a version, and runs nothing unverified.

An unpinned linter is what turned `main` red on 2026-07-30 and kept it red:
`uv tool install ty` and `uv tool install ruff` silently followed upstream, and
the first release with a new rule failed a gate nobody had changed. The
CodeScene installer had the mirror-image problem: it was piped straight into
`bash`, so the digest comparison that followed guarded code that had already
run, against a file the pipe had never written.

Reviewing a workflow by eye does not catch the next one, so both are contracts.
Every assertion matches the command in the workflow rather than a comment or a
step name near it, and each is mutation-tested by a sibling test.
"""

from __future__ import annotations

import re
import typing as typ
from pathlib import Path

import pytest

if typ.TYPE_CHECKING:
    import collections.abc as cabc

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"
WORKFLOW_TEXT = WORKFLOW.read_text(encoding="utf-8")

# `uv tool install X`, `uv pip install X`, `npm install -g X`. The captured
# group is everything after the subcommand on that line, quotes included.
INSTALL_COMMANDS = (
    re.compile(r"\buv tool install\s+(?P<arguments>.+)$", re.MULTILINE),
    re.compile(r"\buv pip install\s+(?P<arguments>.+)$", re.MULTILINE),
    re.compile(r"\bnpm install -g\s+(?P<arguments>.+)$", re.MULTILINE),
)

# A pinned argument is `name==version` or `name@version` where the version is
# exact. Digits and dots, optionally a pre-release suffix. `latest`, `^0.23`,
# `~=1.2`, `1.*` and any comparator are not versions this accepts, because each
# would reintroduce the drift the pin exists to stop.
EXACT_VERSION = r"\d+(?:\.\d+)+(?:[-.][0-9A-Za-z][0-9A-Za-z.]*)?"
PINNED = re.compile(rf"^@?[A-Za-z0-9._/-]+(?:==|@){EXACT_VERSION}$")
LINE_CONTINUATION = re.compile(r"\\\s*$")
SHELL_VARIABLE = re.compile(r"\$\{[A-Za-z_][A-Za-z0-9_]*\}")

# The CodeScene installer, which is fetched rather than installed by a package
# manager and so needs its own three assertions.
INSTALLER_FILE = "install-cs-coverage-tool.sh"
CURL_TO_BASH = re.compile(r"curl[^\n|]*\|\s*bash")
CURL_TO_FILE = re.compile(rf"curl\b[^\n]*-o\s+{re.escape(INSTALLER_FILE)}")
_QUOTED_FILE = re.escape(INSTALLER_FILE)
DIGEST_CHECK = re.compile(
    rf"\$\{{CODESCENE_CLI_SHA256\}}\s+{_QUOTED_FILE}\"?\s*\|\s*sha256sum -c"
)
DIGEST_REQUIRED = re.compile(r'if \[ -z "\$\{CODESCENE_CLI_SHA256:-\}" \]')
RUN_INSTALLER = re.compile(rf"^\s*bash {re.escape(INSTALLER_FILE)}\b", re.MULTILINE)


def _installed_arguments(text: str) -> cabc.Iterator[tuple[str, str]]:
    """Yield every (install command, package argument) pair in ``text``."""
    for pattern in INSTALL_COMMANDS:
        for match in pattern.finditer(text):
            yield from (
                (match.group(0).strip(), token)
                for token in _package_tokens(
                    text, match.end(), match.group("arguments")
                )
            )


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
            if not token.startswith("-"):
                yield token.strip("\"'")
        if not continues:
            return
        newline = text.find("\n", position + 1)
        if newline == -1:
            return
        remainder = text[position + 1 : newline]
        position = newline


def _resolve_shell_variables(package: str) -> str:
    """Substitute `${VAR}` with a stand-in so the pin shape can be matched."""
    return SHELL_VARIABLE.sub("0.0.0", package)


def _is_pinned(package: str) -> bool:
    """Whether ``package`` names an exact version."""
    return PINNED.match(_resolve_shell_variables(package)) is not None


INSTALLED = list(_installed_arguments(WORKFLOW_TEXT))


class TestToolPins:
    """Every package the workflow installs names an exact version."""

    def test_the_workflow_installs_tools_at_all(self) -> None:
        """Guard the patterns: one that matches nothing would prove nothing."""
        assert INSTALLED

    @pytest.mark.parametrize(
        ("command", "package"),
        INSTALLED,
        ids=lambda value: value.replace(" ", "-"),
    )
    def test_every_installed_tool_is_version_pinned(
        self, command: str, package: str
    ) -> None:
        """Each install argument carries an exact version.

        Parameters
        ----------
        command : str
            The install command as written in the workflow, for the message.
        package : str
            One package argument of that command.
        """
        assert _is_pinned(package), f"{command!r} installs {package!r} without a pin"

    def test_the_contract_rejects_an_unpinned_install(self) -> None:
        """Mutation check: a bare package name must not pass."""
        packages = [
            package
            for _, package in _installed_arguments(
                'run: |\n  uv tool install "mbake"\n'
            )
        ]

        assert packages == ["mbake"]
        assert not _is_pinned(packages[0])

    @pytest.mark.parametrize(
        "selector",
        [
            "markdownlint-cli2@latest",
            "markdownlint-cli2@^0.23",
            "markdownlint-cli2@~0.23.0",
            "slipcover==1.*",
            "slipcover>=1.1.0",
            "ruff==",
        ],
        ids=["latest", "caret", "tilde", "wildcard", "lower-bound", "empty"],
    )
    def test_the_contract_rejects_a_floating_selector(self, selector: str) -> None:
        """A range or a moving tag is not a pin, however it is spelt.

        Parameters
        ----------
        selector : str
            A package selector that names something other than one version.
        """
        assert not _is_pinned(selector)

    @pytest.mark.parametrize(
        "selector",
        [
            "mbake==1.4.6",
            "markdownlint-cli2@0.23.2",
            "@typescript/native-preview@7.0.0-dev.20260707.2",
            "ty==0.0.78",
        ],
        ids=["pypi", "npm", "scoped-npm-prerelease", "two-component"],
    )
    def test_the_contract_accepts_an_exact_version(self, selector: str) -> None:
        """The forms the workflow actually uses must still pass.

        Parameters
        ----------
        selector : str
            A package selector naming exactly one version.
        """
        assert _is_pinned(selector)


class TestCodeSceneInstaller:
    """The CodeScene installer is verified before it is executed."""

    def test_the_installer_is_never_piped_into_a_shell(self) -> None:
        """`curl ... | bash` runs the script before anything can check it."""
        assert not CURL_TO_BASH.search(WORKFLOW_TEXT)

    def test_the_installer_is_downloaded_verified_then_run(self) -> None:
        """The three steps appear, in that order, in the workflow."""
        download = CURL_TO_FILE.search(WORKFLOW_TEXT)
        verify = DIGEST_CHECK.search(WORKFLOW_TEXT)
        execute = RUN_INSTALLER.search(WORKFLOW_TEXT)

        assert download is not None, "the installer is not downloaded to a file"
        assert verify is not None, "the downloaded installer's digest is not checked"
        assert execute is not None, "the downloaded installer is never executed"
        assert download.start() < verify.start() < execute.start(), (
            "the digest must be checked after the download and before the run"
        )

    def test_a_missing_digest_fails_the_step(self) -> None:
        """An absent `CODESCENE_CLI_SHA256` must not mean "skip the check"."""
        assert DIGEST_REQUIRED.search(WORKFLOW_TEXT), (
            "the step must refuse to run when CODESCENE_CLI_SHA256 is unset"
        )

    def test_the_pipe_assertion_rejects_the_shape_it_guards(self) -> None:
        """Mutation check for the pipe assertion."""
        assert CURL_TO_BASH.search(
            "curl -fsSL https://example.test/x.sh | bash -s -- -y"
        )
