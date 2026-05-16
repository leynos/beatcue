"""Tests for BeatCue architecture checker CLI."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

from beatcue.architecture.cli import main as architecture_main

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "architecture"


def test_cli_default_invocation_accepts_current_package(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI returns success and no diagnostics for the current package."""
    exit_code = architecture_main([])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""


def test_cli_none_argv_accepts_current_package(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CLI can read an empty argument list from ``sys.argv``."""
    monkeypatch.setattr(sys, "argv", ["beatcue-architecture"])

    exit_code = architecture_main(None)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""


def test_cli_fixture_policy_reports_fixture_violations(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI renders fixture-policy violations to stderr."""
    package_name = "domain_imports_adapter"
    package = f"tests.fixtures.architecture.{package_name}"

    exit_code = architecture_main([
        "--package",
        package,
        "--root",
        str(FIXTURE_ROOT / package_name),
        "--fixture-policy",
    ])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == (
        "ARCH001: tests.fixtures.architecture.domain_imports_adapter.domain "
        "imports forbidden module "
        "tests.fixtures.architecture.domain_imports_adapter.adapters.outbound "
        "(domain -> outbound_adapter)\n"
    )


def test_cli_fixture_policy_switches_from_default_policy(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Fixture packages are only classified when ``--fixture-policy`` is used."""
    package_name = "domain_imports_adapter"
    package = f"tests.fixtures.architecture.{package_name}"

    exit_code = architecture_main([
        "--package",
        package,
        "--root",
        str(FIXTURE_ROOT / package_name),
    ])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""


def test_cli_reports_missing_root_as_usage_error(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Missing package roots return a CLI usage error."""
    missing_root = tmp_path / "missing"

    exit_code = architecture_main(["--root", str(missing_root)])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert captured.err == (
        f"error: architecture package root does not exist: {missing_root}\n"
    )


def test_cli_rejects_unknown_arguments(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Argparse reports unsupported architecture-checker options."""
    with pytest.raises(SystemExit) as exc_info:
        architecture_main(["--unknown-option"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert captured.out == ""
    assert "unrecognized arguments: --unknown-option" in captured.err


def test_module_entrypoint_accepts_current_package(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The ``python -m beatcue.architecture`` entrypoint checks BeatCue."""
    monkeypatch.setattr(sys, "argv", ["beatcue.architecture"])

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module("beatcue.architecture", run_name="__main__", alter_sys=True)

    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert captured.out == ""
    assert captured.err == ""
