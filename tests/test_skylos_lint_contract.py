"""Behavioural contracts for Skylos dead-code detection."""

from __future__ import annotations

import json
import os
import shutil
import string
import subprocess  # noqa: S404 - contract tests invoke fixed local commands.
import tomllib
import typing as typ
from pathlib import Path
from tempfile import TemporaryDirectory

import hypothesis as hyp
import hypothesis.strategies as st

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_EXPECTED_WHITELIST_NAMES: typ.Final = frozenset[str]()
_EXPECTED_DOCUMENTED_WHITELIST_NAMES: typ.Final = frozenset[str]()
_EXPECTED_ENTRYPOINT_NAMES: typ.Final = frozenset[str]()
_SHELL_ARGUMENT_TEXT: typ.Final = st.builds(
    lambda prefix, content, suffix: prefix + content + suffix,
    st.text(alphabet=" \t", max_size=4),
    st.text(
        alphabet=string.ascii_letters + string.digits + "_$;|&'\"()[]{}*?!\\`",
        min_size=1,
        max_size=40,
    ),
    st.text(alphabet=" \t", max_size=4),
)


def _mapping(value: object, *, subject: str) -> dict[str, object]:
    """Return a TOML object, naming an unexpected configuration subject."""
    assert isinstance(value, dict), f"expected {subject} to be a TOML table"
    return typ.cast("dict[str, object]", value)


def _objects(value: object, *, subject: str) -> list[dict[str, object]]:
    """Return a TOML table array, naming an unexpected configuration subject."""
    assert isinstance(value, list), f"expected {subject} to be a TOML array"
    return [_mapping(item, subject=f"{subject} item") for item in value]


def _text_sequence(value: object, *, subject: str) -> tuple[str, ...]:
    """Return a TOML string array, naming an unexpected configuration subject."""
    assert isinstance(value, list), f"expected {subject} to be a TOML array"
    assert all(isinstance(item, str) for item in value), (
        f"expected {subject} to contain only TOML strings"
    )
    return tuple(typ.cast("list[str]", value))


def _run_skylos_allow(
    *,
    symbol: str | None = None,
    reason: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run an invalid whitelist boundary with WSL's injected ``NAME`` value."""
    environment = {**os.environ, "NAME": "wsl-hostname"}
    environment.pop("REASON", None)
    environment.pop("SYMBOL", None)
    if symbol is not None:
        environment["SYMBOL"] = symbol
    if reason is not None:
        environment["REASON"] = reason
    return subprocess.run(  # noqa: S603 - fixed Make target and arguments.
        (_make_executable(), "skylos-allow"),
        capture_output=True,
        check=False,
        cwd=REPOSITORY_ROOT,
        env=environment,
        text=True,
    )


def _make_executable() -> str:
    """Return the absolute Make executable used by subprocess boundaries."""
    executable = shutil.which("make")
    assert executable is not None, "Skylos contract tests require make on PATH"
    return executable


@hyp.settings(max_examples=20, deadline=None)
@hyp.given(whitespace=st.text(alphabet=" \t", min_size=1, max_size=8))
def test_skylos_allow_rejects_missing_and_whitespace_arguments(
    whitespace: str,
) -> None:
    """The helper must reject missing input before executing Skylos."""
    cases = (
        (None, None, "SYMBOL"),
        ("handler", None, "REASON"),
        (whitespace, "verified runtime caller", "SYMBOL"),
        ("handler", whitespace, "REASON"),
    )

    for symbol, reason, missing_name in cases:
        completed = _run_skylos_allow(symbol=symbol, reason=reason)

        assert completed.returncode == 2, (
            f"Skylos whitelist must reject missing {missing_name} with exit 2"
        )
        assert (
            f"Error: {missing_name} is required for a named whitelist exception"
            in completed.stderr
        ), f"Skylos whitelist must explain the missing {missing_name} value"


@hyp.settings(max_examples=20, deadline=None)
@hyp.example(symbol="$(handler);*", reason='Loaded "$plugin" | registry')
@hyp.given(symbol=_SHELL_ARGUMENT_TEXT, reason=_SHELL_ARGUMENT_TEXT)
def test_skylos_allow_forwards_environment_values_without_mutating_configuration(
    symbol: str,
    reason: str,
) -> None:
    """A recorder must receive exactly the safe Skylos whitelist argument order."""
    pyproject_path = REPOSITORY_ROOT / "pyproject.toml"
    original_configuration = pyproject_path.read_bytes()

    with TemporaryDirectory() as temporary_directory:
        temporary_path = Path(temporary_directory)
        recorder = temporary_path / "skylos-recorder"
        arguments_path = temporary_path / "arguments.json"
        allow_lock = temporary_path / "skylos-allow.lock"
        recorder.write_text(
            "#!/usr/bin/env python3\n"
            "import json\n"
            "import os\n"
            "import sys\n"
            "from pathlib import Path\n"
            "Path(os.environ['SKYLOS_ARGUMENTS_PATH']).write_text(\n"
            "    json.dumps(sys.argv[1:]), encoding='utf-8'\n"
            ")\n",
            encoding="utf-8",
        )
        recorder.chmod(0o755)
        environment = {
            **os.environ,
            "NAME": "wsl-hostname",
            "REASON": reason,
            "SKYLOS_ARGUMENTS_PATH": str(arguments_path),
            "SYMBOL": symbol,
        }
        completed = subprocess.run(  # noqa: S603 - fixed Make target and inputs.
            (
                _make_executable(),
                "--no-print-directory",
                f"SKYLOS_CLI={recorder}",
                f"SKYLOS_ALLOW_LOCK={allow_lock}",
                "skylos-allow",
            ),
            capture_output=True,
            check=False,
            cwd=REPOSITORY_ROOT,
            env=environment,
            text=True,
        )

        assert completed.returncode == 0, (
            "Skylos whitelist must accept complete environment-provided values: "
            f"{completed.stderr}"
        )
        assert arguments_path.is_file(), (
            "Skylos whitelist recorder must run instead of the real Skylos CLI"
        )
        assert json.loads(arguments_path.read_text(encoding="utf-8")) == [
            "whitelist",
            symbol,
            "--reason",
            reason,
        ], "Skylos whitelist must forward exact subcommand-first arguments"

    assert pyproject_path.read_bytes() == original_configuration, (
        "Skylos whitelist forwarding contract must not mutate pyproject.toml"
    )


def test_skylos_configuration_enables_the_strict_gate() -> None:
    """Skylos configuration must preserve strict gate and exception contracts."""
    with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as configuration_file:
        configuration = tomllib.load(configuration_file)

    tool = _mapping(configuration.get("tool"), subject="tool configuration")
    skylos = _mapping(tool.get("skylos"), subject="Skylos configuration")
    gate = _mapping(skylos.get("gate"), subject="Skylos gate configuration")
    whitelist = _mapping(
        skylos.get("whitelist"), subject="Skylos whitelist configuration"
    )
    documented = _mapping(
        whitelist.get("documented"), subject="Skylos documented whitelist"
    )
    dead_code = _mapping(
        skylos.get("dead_code", {}), subject="Skylos dead-code configuration"
    )

    assert gate.get("strict") is True, (
        "Skylos gate configuration must enable strict mode"
    )
    assert frozenset(
        _text_sequence(whitelist.get("names"), subject="whitelist names")
    ) == (_EXPECTED_WHITELIST_NAMES), (
        "Skylos documented-whitelist contract must require conscious exceptions"
    )
    assert frozenset(documented) == _EXPECTED_DOCUMENTED_WHITELIST_NAMES, (
        "Skylos documented-whitelist reasons must match named exceptions"
    )
    assert all(
        isinstance(reason, str) and reason.strip() for reason in documented.values()
    ), "Skylos documented-whitelist reasons must contain explanatory text"

    entrypoints = _objects(
        dead_code.get("entrypoints", []), subject="Skylos dead-code entrypoints"
    )
    entrypoint_names = frozenset(
        name
        for entrypoint in entrypoints
        for name in _text_sequence(
            entrypoint.get("full_name"), subject="Skylos entry-point full name"
        )
    )
    assert entrypoint_names == _EXPECTED_ENTRYPOINT_NAMES, (
        "Skylos entry-point contract must require conscious runtime boundaries"
    )
