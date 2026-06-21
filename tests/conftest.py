"""Shared fixtures and helpers for BeatCue tests."""

from __future__ import annotations

import tomllib
import typing as typ
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PRODUCTION_BOUNDARY_GROUPS: tuple[tuple[str, str], ...] = (
    ("beatcue.domain", "domain"),
    ("beatcue.application", "application"),
    ("beatcue.adapters", "adapter"),
    ("beatcue.adapters.inbound", "inbound_adapter"),
    ("beatcue.adapters.outbound", "outbound_adapter"),
    ("beatcue.config", "composition_root"),
)


class HecateGroup(typ.TypedDict):
    """One group entry from the [[tool.hecate.groups]] TOML array."""

    name: str
    prefixes: list[str]
    allowed: list[str]


class HecatePolicy(typ.TypedDict):
    """The [tool.hecate] section of pyproject.toml."""

    root_packages: list[str]
    include_external_packages: bool
    default_rule_id: str
    groups: list[HecateGroup]


@lru_cache(maxsize=1)
def hecate_policy() -> HecatePolicy:
    """Read the production Hecate policy from pyproject.toml (cached).

    Raises
    ------
    FileNotFoundError
        If pyproject.toml is absent from the project root.
    KeyError
        If the [tool.hecate] section is missing from pyproject.toml.
    """
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    return typ.cast("HecatePolicy", pyproject["tool"]["hecate"])


def hecate_group_for(module_name: str) -> HecateGroup | None:
    """Return the configured Hecate group that best matches a module name."""
    groups = hecate_policy()["groups"]
    matching_groups = [
        group
        for group in groups
        if any(
            module_name == prefix or module_name.startswith(f"{prefix}.")
            for prefix in group["prefixes"]
        )
    ]
    return max(
        matching_groups,
        key=lambda group: max(
            len(prefix)
            for prefix in group["prefixes"]
            if module_name == prefix or module_name.startswith(f"{prefix}.")
        ),
        default=None,
    )
