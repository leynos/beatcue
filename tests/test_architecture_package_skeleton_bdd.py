"""Behavioural tests for the production architecture package skeleton."""

from __future__ import annotations

import importlib

from pytest_bdd import given, scenario, then, when

from beatcue.architecture import ArchitectureCheckResult, check_architecture
from beatcue.architecture.policy import ArchitecturePolicy, ModuleGroup, default_policy

_BOUNDARY_GROUPS: dict[str, str] = {
    "beatcue.domain": "domain",
    "beatcue.application": "application",
    "beatcue.adapters": "adapter",
    "beatcue.adapters.inbound": "inbound_adapter",
    "beatcue.adapters.outbound": "outbound_adapter",
    "beatcue.config": "composition_root",
}


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
def run_production_architecture_check() -> ArchitectureCheckResult:
    """Run the production architecture checker."""
    return check_architecture()


@then("the domain, application, adapter, and config packages are classified")
def boundary_packages_are_classified() -> None:
    """Verify production boundary packages map to the intended groups."""
    policy = default_policy()
    for module_name, group_name in _BOUNDARY_GROUPS.items():
        group = _classified_group(policy, module_name)
        assert group.name == group_name, (
            f"Module {module_name!r} classified as {group.name!r}, "
            f"expected {group_name!r}"
        )


@then("the architecture checker reports no production boundary violations")
def architecture_checker_reports_no_violations(
    architecture_check_result: ArchitectureCheckResult,
) -> None:
    """Verify that the production package passes the architecture fitness check."""
    rendered = "\n".join(
        violation.render() for violation in architecture_check_result.violations
    )
    assert architecture_check_result.ok, rendered


def _classified_group(
    policy: ArchitecturePolicy,
    module_name: str,
) -> ModuleGroup:
    """Return the architecture group for a required production package."""
    group = policy.group_for(module_name)
    if group is None:
        msg = f"No group found for module {module_name!r}"
        raise ValueError(msg)
    return group
