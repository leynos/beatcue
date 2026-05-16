"""Shared import-resolution helpers for architecture checks."""

from __future__ import annotations

import typing as typ

if typ.TYPE_CHECKING:
    import ast
    from pathlib import Path


def compute_module_name(root: Path, package: str, source_path: Path) -> str:
    """Derive the dotted module name from a source path."""
    relative = source_path.relative_to(root).with_suffix("")
    parts = tuple(part for part in relative.parts if part != "__init__")
    if not parts:
        return package
    return ".".join((package, *parts))


def resolve_import_from(
    node: ast.ImportFrom,
    source_path: Path,
    importing_module: str,
) -> str | None:
    """Resolve an ``ImportFrom`` node to an absolute module name."""
    if node.level:
        resolved_module = relative_import_base(node, source_path, importing_module)
        if node.module:
            resolved_module = (
                f"{resolved_module}.{node.module}" if resolved_module else node.module
            )
    else:
        resolved_module = node.module or ""

    return resolved_module or None


def relative_import_base(
    node: ast.ImportFrom,
    source_path: Path,
    importing_module: str,
) -> str:
    """Compute the base module for a relative import."""
    parent_parts = importing_module.split(".")
    if source_path.name == "__init__.py":
        module_parts = parent_parts
    else:
        module_parts = parent_parts[:-1]
    drop_count = node.level - 1
    if drop_count:
        # Excessive relative levels intentionally collapse to an empty base.
        module_parts = module_parts[:-drop_count]
    return ".".join(module_parts)
