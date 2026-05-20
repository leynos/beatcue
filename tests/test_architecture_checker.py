"""Tests for BeatCue's Hecate architecture policy."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from hecate.cli import main as hecate_main

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "architecture"


def _fixture_policy(package: str) -> str:
    """Build a Hecate policy for one fixture package."""
    return textwrap.dedent(f"""
        [tool.hecate]
        root_packages = ["{package}"]
        default_rule_id = "ARCH001"

        [[tool.hecate.groups]]
        name = "composition_root"
        prefixes = ["{package}.config"]
        allowed = [
            "adapter",
            "application",
            "composition_root",
            "domain",
            "inbound_adapter",
            "infrastructure",
            "outbound_adapter",
        ]

        [[tool.hecate.groups]]
        name = "domain"
        prefixes = ["{package}.domain"]
        allowed = ["domain"]

        [[tool.hecate.groups]]
        name = "application"
        prefixes = ["{package}.application"]
        allowed = ["application", "domain"]

        [[tool.hecate.groups]]
        name = "inbound_adapter"
        prefixes = ["{package}.cli", "{package}.adapters.inbound"]
        allowed = ["inbound_adapter", "composition_root", "application", "domain"]

        [[tool.hecate.groups]]
        name = "outbound_adapter"
        prefixes = ["{package}.adapters.outbound"]
        allowed = [
            "outbound_adapter",
            "adapter",
            "application",
            "domain",
            "infrastructure",
        ]

        [[tool.hecate.groups]]
        name = "adapter"
        prefixes = ["{package}.adapters"]
        allowed = [
            "adapter",
            "application",
            "domain",
            "infrastructure",
            "outbound_adapter",
        ]

        [[tool.hecate.groups]]
        name = "infrastructure"
        prefixes = [
            "cmdmox",
            "cuprum",
            "cv2",
            "cyclopts",
            "librosa",
            "rich",
            "transformers",
        ]
        allowed = ["infrastructure"]
        """)


def _write_fixture_policy(tmp_path: Path, package: str) -> Path:
    """Write a temporary Hecate config for one fixture package."""
    config_path = tmp_path / "hecate.toml"
    config_path.write_text(_fixture_policy(package), encoding="utf-8")
    return config_path


@pytest.mark.parametrize(
    ("package_name", "expected_parts"),
    [
        (
            "domain_imports_adapter",
            (
                "ARCH001",
                "domain_imports_adapter.domain",
                "domain_imports_adapter.adapters.outbound",
                "domain -> outbound_adapter",
            ),
        ),
        (
            "application_imports_adapter",
            (
                "ARCH001",
                "application_imports_adapter.application",
                "application_imports_adapter.adapters.outbound",
                "application -> outbound_adapter",
            ),
        ),
        (
            "application_imports_reexported_adapter",
            (
                "ARCH001",
                "application_imports_reexported_adapter.application",
                "application_imports_reexported_adapter.adapters.outbound",
                "application -> outbound_adapter",
            ),
        ),
        (
            "application_imports_star_reexported_adapter",
            (
                "ARCH001",
                "application_imports_star_reexported_adapter.application",
                "application_imports_star_reexported_adapter.adapters",
                "application -> adapter",
            ),
        ),
        (
            "inbound_cli_imports_outbound_adapter",
            (
                "ARCH001",
                "inbound_cli_imports_outbound_adapter.cli",
                "inbound_cli_imports_outbound_adapter.adapters.outbound",
                "inbound_adapter -> outbound_adapter",
            ),
        ),
    ],
)
def test_hecate_reports_fixture_boundary_violations(
    package_name: str,
    expected_parts: tuple[str, ...],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Forbidden fixture imports produce stable Hecate diagnostics."""
    package = f"tests.fixtures.architecture.{package_name}"
    config_path = _write_fixture_policy(tmp_path, package)

    exit_code = hecate_main([
        "check",
        "--config",
        str(config_path),
        "--package",
        package,
        "--root",
        str(FIXTURE_ROOT / package_name),
    ])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert not captured.err
    for expected_part in expected_parts:
        assert expected_part in captured.out


@pytest.mark.parametrize(
    "package_name",
    [
        "application_imports_domain_port",
        "composition_root_wires_adapters",
        "inbound_cli_imports_config",
    ],
)
def test_hecate_accepts_allowed_fixture_graphs(
    package_name: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Allowed fixture imports do not produce Hecate violations."""
    package = f"tests.fixtures.architecture.{package_name}"
    config_path = _write_fixture_policy(tmp_path, package)

    exit_code = hecate_main([
        "check",
        "--config",
        str(config_path),
        "--package",
        package,
        "--root",
        str(FIXTURE_ROOT / package_name),
    ])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "hecate: architecture check passed\n"
    assert not captured.err


def test_hecate_accepts_current_beatcue_package(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The current BeatCue skeleton follows the configured boundaries."""
    exit_code = hecate_main(["check", "--format", "text"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "hecate: architecture check passed\n"
    assert not captured.err


def test_hecate_reports_missing_package_root_as_configuration_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing package roots fail before import scanning starts."""
    package = "sample"
    config_path = _write_fixture_policy(tmp_path, package)
    missing_root = tmp_path / "missing"

    exit_code = hecate_main([
        "check",
        "--config",
        str(config_path),
        "--package",
        package,
        "--root",
        str(missing_root),
    ])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert not captured.out
    assert f"package root {missing_root} is not a directory" in captured.err
