"""Static import checker for BeatCue hexagonal architecture boundaries."""

from __future__ import annotations

import ast
import dataclasses as dc
import typing as typ
from pathlib import Path

from ._imports import compute_module_name, resolve_import_from
from .policy import ArchitecturePolicy, ModuleGroup, default_policy
from .reexports import build_reexport_index

if typ.TYPE_CHECKING:
    import collections.abc as cabc


@dc.dataclass(frozen=True, slots=True)
class ArchitectureViolation:
    """A forbidden import between two classified architecture groups."""

    rule_id: str
    importer: str
    imported: str
    importer_group: str
    imported_group: str

    def render(self) -> str:
        """Render a stable single-line diagnostic."""
        return (
            f"{self.rule_id}: {self.importer} imports forbidden module "
            f"{self.imported} ({self.importer_group} -> {self.imported_group})"
        )


@dc.dataclass(frozen=True, slots=True)
class ArchitectureCheckResult:
    """Result from checking one package tree."""

    violations: tuple[ArchitectureViolation, ...]

    @property
    def ok(self) -> bool:
        """Return whether the architecture check passed."""
        return not self.violations


@dc.dataclass(frozen=True, slots=True)
class _ModuleContext:
    """Bundled per-module context for violation scanning."""

    source_path: Path
    module_name: str
    reexport_index: dict[str, str]
    star_reexport_index: dict[str, tuple[tuple[str, str], ...]]


def check_architecture(
    *,
    package_root: Path | str = Path("beatcue"),
    package: str = "beatcue",
    policy: ArchitecturePolicy | None = None,
) -> ArchitectureCheckResult:
    """Check import directions under one package root.

    Parameters
    ----------
    package_root
        Filesystem root containing the package to scan. Defaults to
        ``Path("beatcue")``.
    package
        Dotted package name that corresponds to ``package_root``. Defaults to
        ``"beatcue"``.
    policy
        Optional architecture policy. When omitted, BeatCue's
        ``default_policy()`` is used.

    Returns
    -------
    ArchitectureCheckResult
        Check result whose ``violations`` field is a tuple of
        ``ArchitectureViolation`` values.

    Raises
    ------
    OSError
        Propagated if package source files cannot be read.
    SyntaxError
        Propagated if a scanned Python source file cannot be parsed.

    """
    root = Path(package_root)
    active_policy = default_policy() if policy is None else policy
    reexport_index = build_reexport_index(root, package)
    star_reexport_index = _group_reexports_by_module(reexport_index)
    violations: list[ArchitectureViolation] = []
    for source_path in sorted(root.rglob("*.py")):
        resolved_module_name = compute_module_name(root, package, source_path)
        importer_group = active_policy.group_for(resolved_module_name)
        if importer_group is None:
            continue
        ctx = _ModuleContext(
            source_path=source_path,
            module_name=resolved_module_name,
            reexport_index=reexport_index,
            star_reexport_index=star_reexport_index,
        )
        violations.extend(_violations_for_module(ctx, importer_group, active_policy))
    return ArchitectureCheckResult(violations=tuple(violations))


def _violations_for_module(
    ctx: _ModuleContext,
    importer_group: ModuleGroup,
    active_policy: ArchitecturePolicy,
) -> list[ArchitectureViolation]:
    """Return all boundary violations for one module's imports."""
    violations: list[ArchitectureViolation] = []
    for imported_module in _iter_imported_modules(ctx):
        imported_group = active_policy.group_for(imported_module)
        if imported_group is None:
            continue
        if imported_group.name in importer_group.allowed_groups:
            continue
        violations.append(
            ArchitectureViolation(
                rule_id=active_policy.rule_id,
                importer=ctx.module_name,
                imported=imported_module,
                importer_group=importer_group.name,
                imported_group=imported_group.name,
            )
        )
    return violations


def _iter_imported_modules(ctx: _ModuleContext) -> cabc.Iterator[str]:
    """Yield every imported module name found in one source file."""
    tree = ast.parse(
        ctx.source_path.read_text(encoding="utf-8"), filename=str(ctx.source_path)
    )
    for node in ast.walk(tree):
        match node:
            case ast.Import():
                yield from _iter_direct_imports(node)
            case ast.ImportFrom():
                yield from _iter_from_imports(node, ctx)


def _group_reexports_by_module(
    reexport_index: dict[str, str],
) -> dict[str, tuple[tuple[str, str], ...]]:
    """Group re-export origins by the module that exposes them."""
    grouped: dict[str, list[tuple[str, str]]] = {}
    for exported_symbol, resolved_reexport in reexport_index.items():
        module, _, _symbol = exported_symbol.rpartition(".")
        grouped.setdefault(module, []).append((exported_symbol, resolved_reexport))
    return {module: tuple(sorted(reexports)) for module, reexports in grouped.items()}


def _iter_direct_imports(node: ast.Import) -> cabc.Iterator[str]:
    """Yield module names from a bare ``import`` statement."""
    for alias in node.names:
        yield alias.name


def _iter_from_imports(node: ast.ImportFrom, ctx: _ModuleContext) -> cabc.Iterator[str]:
    """Yield module names from a ``from ... import ...`` statement."""
    imported_module = resolve_import_from(node, ctx.source_path, ctx.module_name)
    if imported_module is None:
        return
    yield imported_module
    for alias in node.names:
        if alias.name == "*":
            yield from _iter_star_reexports(imported_module, ctx.star_reexport_index)
            continue
        imported_symbol = f"{imported_module}.{alias.name}"
        yield imported_symbol
        if resolved_reexport := ctx.reexport_index.get(imported_symbol):
            yield resolved_reexport


def _iter_star_reexports(
    imported_module: str,
    star_reexport_index: dict[str, tuple[tuple[str, str], ...]],
) -> cabc.Iterator[str]:
    """Yield all re-export origins for a star import of one module."""
    for exported_symbol, resolved_reexport in star_reexport_index.get(
        imported_module,
        (),
    ):
        yield exported_symbol
        yield resolved_reexport
