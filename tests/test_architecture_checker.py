"""Tests for BeatCue's Hecate architecture policy."""

from __future__ import annotations

import json
import tomllib
import typing as typ
from pathlib import Path

import pytest
from hecate.cli import main as hecate_main

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "architecture"
BEATCUE_PACKAGE = "beatcue"


def _hecate_policy() -> dict[str, typ.Any]:
    """Read the production Hecate policy from pyproject.toml."""
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    return dict(pyproject["tool"]["hecate"])


def _fixture_prefix(prefix: str, package: str) -> str:
    """Map production BeatCue package prefixes onto one fixture package."""
    if prefix == BEATCUE_PACKAGE:
        return package
    if prefix.startswith(f"{BEATCUE_PACKAGE}."):
        return f"{package}{prefix.removeprefix(BEATCUE_PACKAGE)}"
    return prefix


def _fixture_policy(package: str) -> str:
    """Build a Hecate policy for one fixture package from production policy."""
    policy = _hecate_policy()
    lines = [
        "[tool.hecate]",
        f"root_packages = [{json.dumps(package)}]",
        f"default_rule_id = {json.dumps(policy['default_rule_id'])}",
        "",
    ]

    for group in policy["groups"]:
        group_mapping = _typed_mapping(group)
        prefixes = [
            _fixture_prefix(prefix, package)
            for prefix in _typed_sequence(group_mapping["prefixes"])
        ]
        allowed = _typed_sequence(group_mapping["allowed"])
        lines.extend([
            "[[tool.hecate.groups]]",
            f"name = {json.dumps(group_mapping['name'])}",
            f"prefixes = {_toml_string_array(prefixes)}",
            f"allowed = {_toml_string_array(allowed)}",
            "",
        ])

    return "\n".join(lines)


def _typed_mapping(value: object) -> dict[str, typ.Any]:
    """Narrow parsed TOML group values for static analysis."""
    assert isinstance(value, dict)
    return value


def _typed_sequence(value: object) -> list[str]:
    """Narrow parsed TOML arrays for static analysis."""
    assert isinstance(value, list)
    assert all(isinstance(item, str) for item in value)
    return value


def _toml_string_array(values: list[str]) -> str:
    """Render a compact TOML string array."""
    return f"[{', '.join(json.dumps(value) for value in values)}]"


def _write_fixture_policy(tmp_path: Path, package: str) -> Path:
    """Write a temporary Hecate config for one fixture package."""
    config_path = tmp_path / "hecate.toml"
    config_path.write_text(_fixture_policy(package), encoding="utf-8")
    return config_path


@pytest.mark.parametrize(
    ("package_name", "expected_diagnostics"),
    [
        (
            "domain_imports_adapter",
            (
                (
                    (
                        "ARCH001",
                        "domain_imports_adapter.domain",
                        "domain_imports_adapter.adapters.outbound",
                        "domain -> outbound_adapter",
                    ),
                    2,
                ),
            ),
        ),
        (
            "application_imports_adapter",
            (
                (
                    (
                        "ARCH001",
                        "application_imports_adapter.application",
                        "application_imports_adapter.adapters.outbound",
                        "application -> outbound_adapter",
                    ),
                    2,
                ),
            ),
        ),
        (
            "application_imports_reexported_adapter",
            (
                (
                    (
                        "ARCH001",
                        "application_imports_reexported_adapter.application",
                        "application_imports_reexported_adapter.adapters",
                        "application -> adapter",
                    ),
                    2,
                ),
                (
                    (
                        "ARCH001",
                        "application_imports_reexported_adapter.application",
                        "application_imports_reexported_adapter.adapters.outbound",
                        "application -> outbound_adapter",
                    ),
                    1,
                ),
            ),
        ),
        (
            "application_imports_star_reexported_adapter",
            (
                (
                    (
                        "ARCH001",
                        "application_imports_star_reexported_adapter.application",
                        "application_imports_star_reexported_adapter.adapters",
                        "application -> adapter",
                    ),
                    2,
                ),
            ),
        ),
        (
            "inbound_cli_imports_outbound_adapter",
            (
                (
                    (
                        "ARCH001",
                        "inbound_cli_imports_outbound_adapter.cli",
                        "inbound_cli_imports_outbound_adapter.adapters.outbound",
                        "inbound_adapter -> outbound_adapter",
                    ),
                    2,
                ),
            ),
        ),
    ],
)
def test_hecate_reports_fixture_boundary_violations(
    package_name: str,
    expected_diagnostics: tuple[tuple[tuple[str, ...], int], ...],
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
    violation_lines = [
        line for line in captured.out.splitlines() if line.startswith("ARCH001:")
    ]
    expected_violation_count = sum(count for _, count in expected_diagnostics)
    assert len(violation_lines) == expected_violation_count, (
        f"Expected {expected_violation_count} violation lines, "
        f"found {len(violation_lines)}.\nstdout:\n{captured.out}"
    )
    for expected_parts, expected_count in expected_diagnostics:
        matching_violation_lines = [
            line
            for line in violation_lines
            if all(expected_part in line for expected_part in expected_parts)
        ]
        assert len(matching_violation_lines) == expected_count, (
            "Expected violation lines matching "
            f"{expected_parts!r}: {expected_count}, found "
            f"{len(matching_violation_lines)}.\nstdout:\n{captured.out}"
        )


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
    assert "architecture check passed" in captured.out
    assert not captured.err


def test_hecate_accepts_current_beatcue_package(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The current BeatCue skeleton follows the configured boundaries."""
    exit_code = hecate_main(["check", "--format", "text"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "architecture check passed" in captured.out
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


def test_hecate_reports_file_package_root_as_configuration_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """File package roots fail before import scanning starts."""
    package = "sample"
    config_path = _write_fixture_policy(tmp_path, package)
    file_root = tmp_path / "not_a_directory.py"
    file_root.write_text("print('not a package root')\n", encoding="utf-8")

    exit_code = hecate_main([
        "check",
        "--config",
        str(config_path),
        "--package",
        package,
        "--root",
        str(file_root),
    ])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert not captured.out
    assert f"package root {file_root} is not a directory" in captured.err
