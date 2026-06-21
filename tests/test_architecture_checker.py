"""Tests for BeatCue's Hecate architecture policy."""

from __future__ import annotations

import importlib
import json
import typing as typ
from pathlib import Path

import pytest
from conftest import (
    PRODUCTION_BOUNDARY_GROUPS,
    hecate_group_for,
    hecate_policy,
)
from hecate.cli import main as hecate_main

if typ.TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "architecture"
BEATCUE_PACKAGE = "beatcue"


def _fixture_prefix(prefix: str, package: str) -> str:
    """Map production BeatCue package prefixes onto one fixture package."""
    if prefix == BEATCUE_PACKAGE:
        return package
    if prefix.startswith(f"{BEATCUE_PACKAGE}."):
        return f"{package}{prefix.removeprefix(BEATCUE_PACKAGE)}"
    return prefix


def _fixture_policy(package: str) -> str:
    """Build a Hecate policy for one fixture package from production policy."""
    policy = hecate_policy()
    include_external_packages = str(policy["include_external_packages"]).lower()
    lines = [
        "[tool.hecate]",
        f"root_packages = [{json.dumps(package)}]",
        f"include_external_packages = {include_external_packages}",
        f"default_rule_id = {json.dumps(policy['default_rule_id'])}",
        "",
    ]

    for group in policy["groups"]:
        prefixes = [_fixture_prefix(prefix, package) for prefix in group["prefixes"]]
        allowed = group["allowed"]
        lines.extend([
            "[[tool.hecate.groups]]",
            f"name = {json.dumps(group['name'])}",
            f"prefixes = {_toml_string_array(prefixes)}",
            f"allowed = {_toml_string_array(allowed)}",
            "",
        ])

    return "\n".join(lines)


def _toml_string_array(values: list[str]) -> str:
    """Render a compact TOML string array."""
    return f"[{', '.join(json.dumps(value) for value in values)}]"


def _write_fixture_policy(tmp_path: Path, package: str) -> Path:
    """Write a temporary Hecate config for one fixture package."""
    config_path = tmp_path / "hecate.toml"
    config_path.write_text(_fixture_policy(package), encoding="utf-8")
    return config_path


@pytest.mark.parametrize(
    "package_name",
    [
        "domain_imports_adapter",
        "domain_imports_cmd_mox",
        "domain_imports_pil",
        "application_imports_adapter",
        "application_imports_reexported_adapter",
        "application_imports_star_reexported_adapter",
        "inbound_cli_imports_outbound_adapter",
    ],
)
def test_hecate_reports_fixture_boundary_violations(
    package_name: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    snapshot: SnapshotAssertion,
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
    assert exit_code == 1, (
        f"Expected exit code 1, got {exit_code}.\nstdout:\n{captured.out}"
    )
    assert not captured.err, f"Unexpected stderr:\n{captured.err}"
    assert captured.out == snapshot


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
    assert exit_code == 0, f"Expected exit 0, got {exit_code}.\nstdout:\n{captured.out}"
    assert "architecture check passed" in captured.out, (
        f"Expected 'architecture check passed' in stdout:\n{captured.out}"
    )
    assert not captured.err, f"Unexpected stderr:\n{captured.err}"


def test_hecate_accepts_current_beatcue_package(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The current BeatCue skeleton follows the configured boundaries."""
    exit_code = hecate_main(["check", "--format", "text"])

    captured = capsys.readouterr()
    assert exit_code == 0, f"Expected exit 0, got {exit_code}.\nstdout:\n{captured.out}"
    assert "architecture check passed" in captured.out, (
        f"Expected 'architecture check passed' in stdout:\n{captured.out}"
    )
    assert not captured.err, f"Unexpected stderr:\n{captured.err}"


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
    assert exit_code == 2, f"Expected exit 2, got {exit_code}"
    assert not captured.out, f"Unexpected stdout:\n{captured.out}"
    assert f"package root {missing_root} is not a directory" in captured.err, (
        f"Expected directory error in stderr:\n{captured.err}"
    )


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
    assert exit_code == 2, f"Expected exit 2, got {exit_code}"
    assert not captured.out, f"Unexpected stdout:\n{captured.out}"
    assert f"package root {file_root} is not a directory" in captured.err, (
        f"Expected directory error in stderr:\n{captured.err}"
    )


@pytest.mark.parametrize(("module_name", "group_name"), PRODUCTION_BOUNDARY_GROUPS)
def test_production_boundary_packages_match_architecture_groups(
    module_name: str,
    group_name: str,
) -> None:
    """The default architecture policy classifies real boundary packages."""
    group = hecate_group_for(module_name)

    assert group is not None, f"module {module_name!r} not classified by Hecate"
    assert group["name"] == group_name, (
        f"module {module_name!r} classified as {group['name']!r}, "
        f"expected {group_name!r}"
    )


@pytest.mark.parametrize(("module_name", "_group_name"), PRODUCTION_BOUNDARY_GROUPS)
def test_production_boundary_packages_are_importable(
    module_name: str,
    _group_name: str,
) -> None:
    """The production package exposes the planned hexagonal boundaries."""
    module = importlib.import_module(module_name)

    assert module.__name__ == module_name, (
        f"imported {module.__name__!r}, expected {module_name!r}"
    )
