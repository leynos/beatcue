"""Behavioural tests for the production architecture package skeleton."""

from __future__ import annotations

import importlib
import tomllib
import typing as typ
from pathlib import Path

from hecate.cli import main as hecate_main
from pytest_bdd import given, scenario, then, when

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_BOUNDARY_GROUPS: dict[str, str] = {
    "beatcue.domain": "domain",
    "beatcue.application": "application",
    "beatcue.adapters": "adapter",
    "beatcue.adapters.inbound": "inbound_adapter",
    "beatcue.adapters.outbound": "outbound_adapter",
    "beatcue.config": "composition_root",
}


def _hecate_policy() -> dict[str, typ.Any]:
    """Read the production Hecate policy from pyproject.toml."""
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    return dict(pyproject["tool"]["hecate"])


def _typed_mapping(value: object) -> dict[str, typ.Any]:
    """Narrow parsed TOML group values for static analysis."""
    assert isinstance(value, dict)
    return typ.cast("dict[str, typ.Any]", value)


def _typed_sequence(value: object) -> list[str]:
    """Narrow parsed TOML arrays for static analysis."""
    assert isinstance(value, list)
    assert all(isinstance(item, str) for item in value)
    return typ.cast("list[str]", value)


def _hecate_group_for(module_name: str) -> dict[str, typ.Any] | None:
    """Return the configured Hecate group for a production module."""
    groups = [_typed_mapping(group) for group in _hecate_policy()["groups"]]
    matching_groups = [
        group
        for group in groups
        if any(
            module_name == prefix or module_name.startswith(f"{prefix}.")
            for prefix in _typed_sequence(group["prefixes"])
        )
    ]
    return max(
        matching_groups,
        key=lambda group: max(
            len(prefix) for prefix in _typed_sequence(group["prefixes"])
        ),
        default=None,
    )


@scenario(
    "features/architecture_package_skeleton.feature",
    "The production package exposes the hexagonal boundary",
)
def test_production_package_exposes_hexagonal_boundary() -> None:
    """Production boundary packages satisfy the architecture fitness check."""


@given("the BeatCue package skeleton is installed")
def package_skeleton_is_installed() -> None:
    """Verify that the planned production boundary packages can be imported."""
    for module_name in _BOUNDARY_GROUPS:
        importlib.import_module(module_name)


@when(
    "the architecture checker runs against the production package",
    target_fixture="architecture_check_result",
)
def run_production_architecture_check() -> int:
    """Run the production architecture checker."""
    return hecate_main(["check"])


@then("the domain, application, adapter, and config packages are classified")
def boundary_packages_are_classified() -> None:
    """Verify production boundary packages map to the intended groups."""
    for module_name, group_name in _BOUNDARY_GROUPS.items():
        group = _classified_group(module_name)
        assert group["name"] == group_name, (
            f"Module {module_name!r} classified as {group['name']!r}, "
            f"expected {group_name!r}"
        )


@then("the architecture checker reports no production boundary violations")
def architecture_checker_reports_no_violations(
    architecture_check_result: int,
) -> None:
    """Verify that the production package passes the architecture fitness check."""
    assert architecture_check_result == 0


def _classified_group(module_name: str) -> dict[str, typ.Any]:
    """Return the architecture group for a required production package."""
    group = _hecate_group_for(module_name)
    if group is None:
        msg = f"No group found for module {module_name!r}"
        raise ValueError(msg)
    return group
