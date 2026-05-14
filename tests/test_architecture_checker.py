"""Tests for BeatCue architecture checker policy enforcement."""

from __future__ import annotations

import ast
import keyword
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from beatcue.architecture import check_architecture, fixture_policy
from beatcue.architecture._imports import compute_module_name, relative_import_base

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "architecture"
type ExpectedViolation = tuple[str, str, str, str, str]
_IDENTIFIER = st.from_regex(r"[a-z][a-z0-9_]{0,12}", fullmatch=True).filter(
    lambda value: not keyword.iskeyword(value)
)


@pytest.mark.parametrize(
    ("package_name", "expected_parts", "expected_violations"),
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
            (
                (
                    "ARCH001",
                    "tests.fixtures.architecture.domain_imports_adapter.domain",
                    "tests.fixtures.architecture.domain_imports_adapter.adapters.outbound",
                    "domain",
                    "outbound_adapter",
                ),
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
            (
                (
                    "ARCH001",
                    "tests.fixtures.architecture.application_imports_adapter.application",
                    "tests.fixtures.architecture.application_imports_adapter.adapters.outbound",
                    "application",
                    "outbound_adapter",
                ),
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
            (
                (
                    "ARCH001",
                    "tests.fixtures.architecture.application_imports_reexported_adapter.application",
                    "tests.fixtures.architecture.application_imports_reexported_adapter.adapters",
                    "application",
                    "adapter",
                ),
                (
                    "ARCH001",
                    "tests.fixtures.architecture.application_imports_reexported_adapter.application",
                    "tests.fixtures.architecture.application_imports_reexported_adapter.adapters.outbound",
                    "application",
                    "outbound_adapter",
                ),
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
            (
                (
                    "ARCH001",
                    "tests.fixtures.architecture.application_imports_star_reexported_adapter.application",
                    "tests.fixtures.architecture.application_imports_star_reexported_adapter.adapters",
                    "application",
                    "adapter",
                ),
                (
                    "ARCH001",
                    "tests.fixtures.architecture.application_imports_star_reexported_adapter.application",
                    "tests.fixtures.architecture.application_imports_star_reexported_adapter.adapters.outbound",
                    "application",
                    "outbound_adapter",
                ),
            ),
        ),
        (
            "inbound_cli_imports_outbound_adapter",
            (
                "ARCH001",
                "inbound_cli_imports_outbound_adapter.cli",
                "inbound_cli_imports_outbound_adapter.adapters.outbound",
                "inbound_adapter",
                "outbound_adapter",
            ),
            (
                (
                    "ARCH001",
                    "tests.fixtures.architecture.inbound_cli_imports_outbound_adapter.cli",
                    "tests.fixtures.architecture.inbound_cli_imports_outbound_adapter.adapters.outbound",
                    "inbound_adapter",
                    "outbound_adapter",
                ),
            ),
        ),
    ],
)
def test_checker_reports_fixture_boundary_violations(
    package_name: str,
    expected_parts: tuple[str, ...],
    expected_violations: tuple[ExpectedViolation, ...],
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
    assert len(result.violations) == len(expected_violations), (
        f"expected {len(expected_violations)} violations, "
        f"got {len(result.violations)}: {rendered!r}"
    )
    for violation, expected_violation in zip(
        result.violations,
        expected_violations,
        strict=True,
    ):
        assert (
            violation.rule_id,
            violation.importer,
            violation.imported,
            violation.importer_group,
            violation.imported_group,
        ) == expected_violation


@pytest.mark.parametrize(
    "package_name",
    [
        "application_imports_domain_port",
        "composition_root_wires_adapters",
        "inbound_cli_imports_config",
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


def test_checker_rejects_missing_package_root(tmp_path: Path) -> None:
    """Missing package roots fail fast instead of producing a false pass."""
    missing_root = tmp_path / "missing"

    with pytest.raises(FileNotFoundError, match="architecture package root"):
        check_architecture(package_root=missing_root)


def test_checker_rejects_file_package_root(tmp_path: Path) -> None:
    """File package roots fail fast before import scanning starts."""
    file_root = tmp_path / "module.py"
    file_root.write_text("", encoding="utf-8")

    with pytest.raises(NotADirectoryError, match="architecture package root"):
        check_architecture(package_root=file_root)


def test_fixture_policy_keeps_inbound_and_outbound_permissions_distinct() -> None:
    """Inbound and outbound adapters have separate dependency directions."""
    policy = fixture_policy("tests.fixtures.architecture.package")

    inbound_group = policy.group_for("tests.fixtures.architecture.package.cli")
    outbound_group = policy.group_for(
        "tests.fixtures.architecture.package.adapters.outbound"
    )

    assert inbound_group is not None
    assert outbound_group is not None
    assert "composition_root" in inbound_group.allowed_groups
    assert "outbound_adapter" not in inbound_group.allowed_groups
    assert "outbound_adapter" in outbound_group.allowed_groups
    assert "inbound_adapter" not in outbound_group.allowed_groups
    assert "adapter" not in outbound_group.allowed_groups


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


@pytest.mark.parametrize(
    ("source_path", "importing_module", "level", "expected"),
    [
        (
            Path("module.py"),
            "tests.fixtures.architecture.package.module",
            1,
            "tests.fixtures.architecture.package",
        ),
        (
            Path("module.py"),
            "tests.fixtures.architecture.package.module",
            2,
            "tests.fixtures.architecture",
        ),
        (
            Path("__init__.py"),
            "tests.fixtures.architecture.package",
            1,
            "tests.fixtures.architecture.package",
        ),
        (
            Path("__init__.py"),
            "tests.fixtures.architecture.package",
            2,
            "tests.fixtures.architecture",
        ),
    ],
)
def test_relative_import_base_handles_valid_module_and_package_levels(
    source_path: Path,
    importing_module: str,
    level: int,
    expected: str,
) -> None:
    """Relative import helpers derive bases for module and package imports."""
    node = ast.ImportFrom(module=None, names=[], level=level)

    result = relative_import_base(node, source_path, importing_module)

    assert result == expected


@given(
    parts=st.lists(_IDENTIFIER, min_size=1, max_size=5), source_kind=st.integers(0, 1)
)
def test_compute_module_name_round_trips_source_paths(
    parts: list[str],
    source_kind: int,
) -> None:
    """Module-name computation preserves dotted package-relative paths."""
    root = Path("pkg")
    source_path = (
        root.joinpath(*parts, "__init__.py")
        if source_kind
        else root.joinpath(*parts).with_suffix(".py")
    )

    result = compute_module_name(root, "pkg", source_path)

    assert result == ".".join(("pkg", *parts))


@given(
    depth=st.integers(min_value=1, max_value=6),
    level=st.integers(min_value=1, max_value=8),
    source_kind=st.integers(0, 1),
)
def test_relative_import_base_matches_package_depth(
    depth: int,
    level: int,
    source_kind: int,
) -> None:
    """Relative import bases collapse according to module package depth."""
    parts = tuple(f"p{index}" for index in range(depth))
    importing_module = ".".join(parts)
    source_path = Path("__init__.py") if source_kind else Path(f"{parts[-1]}.py")
    module_parts = parts if source_kind else parts[:-1]
    drop_count = level - 1
    expected_parts = module_parts[:-drop_count] if drop_count else module_parts
    node = ast.ImportFrom(module=None, names=[], level=level)

    result = relative_import_base(node, source_path, importing_module)

    assert result == ".".join(expected_parts)


@given(suffix=st.lists(_IDENTIFIER, min_size=0, max_size=3))
def test_fixture_policy_classifies_group_prefix_descendants(
    suffix: list[str],
) -> None:
    """Architecture group membership follows the first matching prefix."""
    policy = fixture_policy("tests.fixtures.architecture.package")

    for group in policy.groups:
        for prefix in group.module_prefixes:
            module = ".".join((prefix, *suffix)) if suffix else prefix

            result = policy.group_for(module)
            matching_groups = tuple(
                candidate for candidate in policy.groups if candidate.contains(module)
            )

            assert result == matching_groups[0]
