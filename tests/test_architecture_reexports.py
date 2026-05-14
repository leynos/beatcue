"""Tests for BeatCue architecture re-export resolution."""

from __future__ import annotations

import ast
import typing as typ

from beatcue.architecture.reexports import _explicit_all_exports, build_reexport_index

if typ.TYPE_CHECKING:
    from pathlib import Path


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


def test_explicit_all_exports_uses_final_assignment() -> None:
    """The final ``__all__`` assignment determines explicit exports."""
    tree = ast.parse(
        "\n".join([
            "__all__ = ['FirstExport']",
            "__all__ = dynamic_exports()",
            "__all__ = ['LastExport']",
        ])
    )

    result = _explicit_all_exports(tree)

    assert result == ("LastExport",)


def test_explicit_all_exports_returns_none_when_final_assignment_is_unresolved() -> (
    None
):
    """A final non-resolvable ``__all__`` statement disables explicit export names."""
    tree = ast.parse(
        "\n".join([
            "__all__ = ['FirstExport']",
            "__all__: list[str]",
        ])
    )

    result = _explicit_all_exports(tree)

    assert result is None
