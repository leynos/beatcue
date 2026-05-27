"""Behavioural tests for the production architecture package skeleton."""

from __future__ import annotations

import importlib

from conftest import PRODUCTION_BOUNDARY_GROUPS
from hecate.cli import main as hecate_main
from pytest_bdd import given, scenario, then, when

_BOUNDARY_GROUPS: dict[str, str] = dict(PRODUCTION_BOUNDARY_GROUPS)


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


@then("the architecture checker reports no production boundary violations")
def architecture_checker_reports_no_violations(
    architecture_check_result: int,
) -> None:
    """Verify that the production package passes the architecture fitness check."""
    assert architecture_check_result == 0, (
        f"Architecture checker exited with {architecture_check_result}, expected 0"
    )
