"""Smoke tests for declared dependency wiring."""

from __future__ import annotations

from importlib import import_module, metadata
from types import ModuleType

import pytest


@pytest.mark.parametrize(
    ("distribution_name", "import_name"),
    [
        ("cmd-mox", "cmd_mox"),
        ("syrupy", "syrupy"),
    ],
)
def test_dev_dependency_import_names_are_resolvable(
    distribution_name: str,
    import_name: str,
) -> None:
    """Installed dev distributions expose the import names used in policy."""
    installed_version = metadata.version(distribution_name)
    imported_module = import_module(import_name)

    assert installed_version, (
        f"Distribution {distribution_name!r} should expose an installed version"
    )
    assert isinstance(imported_module, ModuleType), (
        f"Import {import_name!r} should resolve to a module object"
    )
