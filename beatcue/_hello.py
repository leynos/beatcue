"""Resolve the fastest available hello implementation."""

from __future__ import annotations

import typing as typ
from importlib import import_module

if typ.TYPE_CHECKING:
    import collections.abc as cabc

PACKAGE_NAME: str = "beatcue"
MODULE_NAME: str = f"_{PACKAGE_NAME}_rs"


def _pure_hello() -> cabc.Callable[[], str]:
    from .pure import hello as pure_hello

    return pure_hello


hello: cabc.Callable[[], str]

try:  # pragma: no cover - Rust optional
    rust = import_module(MODULE_NAME)
except (  # pragma: no cover - Python fallback
    ModuleNotFoundError,
    ImportError,
    OSError,
):
    hello = _pure_hello()
else:  # pragma: no cover - Rust optional
    rust_hello = getattr(rust, "hello", None)
    hello = rust_hello if callable(rust_hello) else _pure_hello()

__all__ = ["hello"]
