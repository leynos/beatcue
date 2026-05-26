"""Shared fixtures and helpers for BeatCue tests."""

from __future__ import annotations

import tomllib
import typing as typ
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def hecate_policy() -> dict[str, typ.Any]:
    """Read the production Hecate policy from pyproject.toml (cached)."""
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    return dict(pyproject["tool"]["hecate"])


def typed_mapping(value: object) -> dict[str, typ.Any]:
    """Narrow parsed TOML group values for static analysis."""
    assert isinstance(value, dict), f"Expected dict, got {type(value).__name__}"  # noqa: S101
    return typ.cast("dict[str, typ.Any]", value)


def typed_sequence(value: object) -> list[str]:
    """Narrow parsed TOML arrays for static analysis."""
    assert isinstance(value, list), f"Expected list, got {type(value).__name__}"  # noqa: S101
    assert all(isinstance(item, str) for item in value), (  # noqa: S101
        "Expected all items to be str"
    )
    return typ.cast("list[str]", value)


def hecate_group_for(module_name: str) -> dict[str, typ.Any] | None:
    """Return the configured Hecate group that best matches a module name."""
    groups = [typed_mapping(group) for group in hecate_policy()["groups"]]
    matching_groups = [
        group
        for group in groups
        if any(
            module_name == prefix or module_name.startswith(f"{prefix}.")
            for prefix in typed_sequence(group["prefixes"])
        )
    ]
    return max(
        matching_groups,
        key=lambda group: max(
            len(prefix)
            for prefix in typed_sequence(group["prefixes"])
            if module_name == prefix or module_name.startswith(f"{prefix}.")
        ),
        default=None,
    )
