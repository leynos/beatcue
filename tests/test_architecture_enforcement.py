"""Tests for BeatCue hexagonal architecture enforcement."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

from beatcue.architecture import check_architecture, fixture_policy
from beatcue.architecture._imports import relative_import_base
from beatcue.architecture.cli import main as architecture_main
from beatcue.architecture.reexports import build_reexport_index

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "architecture"
ExpectedViolation = tuple[str, str, str, str, str]


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


def test_reexport_index_resolves_star_imports_from_package_root(
    tmp_path: Path,
) -> None:
    """Package-root star imports resolve through the root ``__init__`` file."""
    package_root = tmp_path / "sample"
    subpackage = package_root / "sub"
    subpackage.mkdir(parents=True)
    (package_root / "__init__.py").write_text(
        "class RootExport: ...\n__all__ = ['RootExport']\n",
        encoding="utf-8",
    )
    (subpackage / "__init__.py").write_text(
        "from sample import *\n",
        encoding="utf-8",
    )

    result = build_reexport_index(package_root, "sample")

    assert result["sample.sub.RootExport"] == "sample.RootExport"


def test_reexport_index_uses_last_resolvable_all_assignment(tmp_path: Path) -> None:
    """Literal ``__all__`` assignments after dynamic ones take precedence."""
    package_root = tmp_path / "sample"
    package_root.mkdir()
    (package_root / "__init__.py").write_text(
        "from .module import *\n",
        encoding="utf-8",
    )
    (package_root / "module.py").write_text(
        "\n".join([
            "class FirstExport: ...",
            "class LastExport: ...",
            "__all__ = dynamic_exports()",
            "__all__ = ['LastExport']",
        ]),
        encoding="utf-8",
    )

    result = build_reexport_index(package_root, "sample")

    assert result == {"sample.LastExport": "sample.module.LastExport"}


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
