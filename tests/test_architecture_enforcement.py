"""Tests for BeatCue hexagonal architecture enforcement."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from beatcue.architecture import check_architecture, fixture_policy
from beatcue.architecture._imports import relative_import_base

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "architecture"


@pytest.mark.parametrize(
    ("package_name", "expected_parts"),
    [
        (
            "domain_imports_adapter",
            (
                "ARCH001",
                "domain_imports_adapter.domain",
                "domain_imports_adapter.adapters.outbound",
                "domain",
                "outbound_adapter",
            ),
        ),
        (
            "application_imports_adapter",
            (
                "ARCH001",
                "application_imports_adapter.application",
                "application_imports_adapter.adapters.outbound",
                "application",
                "outbound_adapter",
            ),
        ),
        (
            "application_imports_reexported_adapter",
            (
                "ARCH001",
                "application_imports_reexported_adapter.application",
                "application_imports_reexported_adapter.adapters.outbound",
                "application",
                "outbound_adapter",
            ),
        ),
        (
            "application_imports_star_reexported_adapter",
            (
                "ARCH001",
                "application_imports_star_reexported_adapter.application",
                "application_imports_star_reexported_adapter.adapters.outbound",
                "application",
                "outbound_adapter",
            ),
        ),
    ],
)
def test_checker_reports_fixture_boundary_violations(
    package_name: str,
    expected_parts: tuple[str, ...],
) -> None:
    """Forbidden fixture imports produce stable architecture diagnostics."""
    package = f"tests.fixtures.architecture.{package_name}"

    result = check_architecture(
        package_root=FIXTURE_ROOT / package_name,
        package=package,
        policy=fixture_policy(package),
    )

    rendered = "\n".join(violation.render() for violation in result.violations)
    assert not result.ok, rendered
    for expected_part in expected_parts:
        assert expected_part in rendered, (
            f"expected {expected_part!r} in architecture diagnostics {rendered!r}"
        )


@pytest.mark.parametrize(
    "package_name",
    [
        "application_imports_domain_port",
        "composition_root_wires_adapters",
    ],
)
def test_checker_accepts_allowed_fixture_graphs(package_name: str) -> None:
    """Allowed fixture imports do not produce architecture violations."""
    package = f"tests.fixtures.architecture.{package_name}"

    result = check_architecture(
        package_root=FIXTURE_ROOT / package_name,
        package=package,
        policy=fixture_policy(package),
    )

    rendered = "\n".join(violation.render() for violation in result.violations)
    assert result.ok, rendered


def test_production_checker_accepts_current_beatcue_package() -> None:
    """The current BeatCue skeleton follows the enforced boundaries."""
    result = check_architecture()

    rendered = "\n".join(violation.render() for violation in result.violations)
    assert result.ok, rendered


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        (2, "tests.fixtures"),
        (3, "tests"),
        (4, ""),
    ],
)
def test_relative_import_base_handles_levels_beyond_module_depth(
    level: int,
    expected: str,
) -> None:
    """Relative import helpers keep returning strings for excessive levels."""
    node = ast.ImportFrom(module=None, names=[], level=level)

    result = relative_import_base(
        node,
        Path("module.py"),
        "tests.fixtures.architecture.module",
    )

    assert isinstance(result, str), (
        "relative_import_base should return a string even when the import level "
        "exceeds the importing module depth"
    )
    assert result == expected
