"""Tests for BeatCue architecture checker CLI."""

from __future__ import annotations

import sys
import typing as typ
from pathlib import Path

from beatcue.architecture.cli import main as architecture_main

if typ.TYPE_CHECKING:
    import pytest

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
    assert "ARCH001" in captured.err
    assert "domain_imports_adapter.domain" in captured.err
    assert "domain_imports_adapter.adapters.outbound" in captured.err


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
