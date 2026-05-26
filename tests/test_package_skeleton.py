"""Tests for the production package skeleton."""

from __future__ import annotations

import ast
import importlib
import keyword
import tomllib
import typing as typ
from pathlib import Path

import pytest
from hecate.cli import main as hecate_main
from hypothesis import given
from hypothesis import strategies as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BEATCUE_PACKAGE = "beatcue"
_PRODUCTION_BOUNDARY_GROUPS: tuple[tuple[str, str], ...] = (
    ("beatcue.domain", "domain"),
    ("beatcue.application", "application"),
    ("beatcue.adapters", "adapter"),
    ("beatcue.adapters.inbound", "inbound_adapter"),
    ("beatcue.adapters.outbound", "outbound_adapter"),
    ("beatcue.config", "composition_root"),
)
_PRODUCTION_BOUNDARY_FILES: tuple[tuple[str, str, Path], ...] = (
    (
        "beatcue.domain",
        "Pure BeatCue domain values, services, and port protocols.",
        PROJECT_ROOT / "beatcue" / "domain" / "__init__.py",
    ),
    (
        "beatcue.application",
        "BeatCue application use cases that orchestrate domain ports.",
        PROJECT_ROOT / "beatcue" / "application" / "__init__.py",
    ),
    (
        "beatcue.adapters",
        "Infrastructure adapter boundary for BeatCue.",
        PROJECT_ROOT / "beatcue" / "adapters" / "__init__.py",
    ),
    (
        "beatcue.adapters.inbound",
        "Driving adapters that invoke BeatCue application services.",
        PROJECT_ROOT / "beatcue" / "adapters" / "inbound" / "__init__.py",
    ),
    (
        "beatcue.adapters.outbound",
        "Driven adapters that implement BeatCue domain-owned ports.",
        PROJECT_ROOT / "beatcue" / "adapters" / "outbound" / "__init__.py",
    ),
    (
        "beatcue.config",
        "Composition root for wiring BeatCue application services and adapters.",
        PROJECT_ROOT / "beatcue" / "config" / "__init__.py",
    ),
)
_IDENTIFIER = st.from_regex(r"[a-z][a-z0-9_]{0,8}", fullmatch=True).filter(
    lambda value: not keyword.iskeyword(value)
)


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


def _write_package_init(package_root: Path, module_name: str, body: str) -> None:
    """Write one package `__init__.py` for a temporary BeatCue package."""
    package_path = package_root.joinpath(*module_name.split(".")[1:])
    package_path.mkdir(parents=True, exist_ok=True)
    (package_path / "__init__.py").write_text(body, encoding="utf-8")


def _has_future_annotations(module_ast: ast.Module) -> bool:
    """Return whether a module imports future annotations."""
    return any(
        isinstance(statement, ast.ImportFrom)
        and statement.module == "__future__"
        and any(alias.name == "annotations" for alias in statement.names)
        for statement in module_ast.body
    )


def _has_empty_all(module_ast: ast.Module) -> bool:
    """Return whether a module assigns an empty `__all__` list."""
    return any(
        isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
        and statement.target.id == "__all__"
        and isinstance(statement.value, ast.List)
        and not statement.value.elts
        for statement in module_ast.body
    )


@pytest.mark.parametrize(
    ("module_name", "expected_docstring", "source_path"),
    _PRODUCTION_BOUNDARY_FILES,
)
def test_production_boundary_init_files_express_only_package_invariants(
    module_name: str,
    expected_docstring: str,
    source_path: Path,
) -> None:
    """Boundary package files keep the intended placeholder contract."""
    module_ast = ast.parse(source_path.read_text(encoding="utf-8"))
    module = importlib.import_module(module_name)

    assert ast.get_docstring(module_ast) == expected_docstring
    assert _has_future_annotations(module_ast)
    assert _has_empty_all(module_ast)
    assert module.__all__ == []


def test_hecate_rejects_temporary_boundary_violation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A domain import from an adapter fails the production Hecate policy."""
    package_root = tmp_path / "beatcue"
    _write_package_init(
        package_root,
        "beatcue.domain",
        "from beatcue.adapters import outbound\n",
    )
    _write_package_init(package_root, "beatcue.adapters", "__all__ = []\n")
    _write_package_init(package_root, "beatcue.adapters.outbound", "__all__ = []\n")

    exit_code = hecate_main([
        "check",
        "--package",
        BEATCUE_PACKAGE,
        "--root",
        str(package_root),
    ])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert not captured.err
    assert "ARCH001:" in captured.out
    assert "beatcue.domain" in captured.out
    assert "beatcue.adapters" in captured.out


@given(
    boundary_group=st.sampled_from(_PRODUCTION_BOUNDARY_GROUPS),
    suffix=st.lists(_IDENTIFIER, min_size=1, max_size=3).map(tuple),
)
def test_production_boundary_descendants_match_architecture_groups(
    boundary_group: tuple[str, str],
    suffix: tuple[str, ...],
) -> None:
    """Generated BeatCue descendants inherit the nearest boundary group."""
    module_name, group_name = boundary_group
    descendant_module_name = f"{module_name}.{'.'.join(suffix)}"
    group = _hecate_group_for(descendant_module_name)

    assert group is not None, (
        f"module {descendant_module_name!r} not classified by Hecate"
    )
    assert group["name"] == group_name, (
        f"module {descendant_module_name!r} classified as {group['name']!r}, "
        f"expected {group_name!r}"
    )
