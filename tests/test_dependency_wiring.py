"""Smoke tests for declared dependency wiring."""

from __future__ import annotations

import tomllib
import typing as typ
from importlib import import_module, metadata
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_314_MARKER = "python_full_version < '3.14'"
ProjectMetadata = typ.TypedDict(
    "ProjectMetadata",
    {"optional-dependencies": dict[str, list[str]]},
)


class HecateGroupMetadata(typ.TypedDict):
    """One Hecate group entry from `pyproject.toml`."""

    name: str
    prefixes: list[str]
    allowed: list[str]


class HecateMetadata(typ.TypedDict):
    """The `[tool.hecate]` metadata needed by dependency-wiring tests."""

    groups: list[HecateGroupMetadata]


class ToolMetadata(typ.TypedDict):
    """The `[tool]` metadata needed by dependency-wiring tests."""

    hecate: HecateMetadata


PyprojectMetadata = typ.TypedDict(
    "PyprojectMetadata",
    {
        "project": ProjectMetadata,
        "dependency-groups": dict[str, list[str]],
        "tool": ToolMetadata,
    },
)


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


def _pyproject() -> PyprojectMetadata:
    """Return parsed project metadata from `pyproject.toml`."""
    return typ.cast(
        "PyprojectMetadata",
        tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text()),
    )


def test_runtime_optional_dependency_groups_match_design() -> None:
    """Runtime extras keep the declared capability groups and marker policy."""
    pyproject = _pyproject()
    project = pyproject["project"]
    optional_dependencies = project["optional-dependencies"]

    assert set(optional_dependencies) == {"core", "media", "editorial", "models"}
    assert optional_dependencies["core"] == [
        "cyclopts>=4.16",
        "rich>=15",
        "cuprum>=0.1.0",
        "msgspec>=0.21",
    ]
    assert optional_dependencies["media"] == [
        "opencv-python-headless>=4.13",
        "scenedetect-headless>=0.7",
        f"librosa>=0.11; {PYTHON_314_MARKER}",
    ]
    assert optional_dependencies["editorial"] == [
        f"OpenTimelineIO>=0.18; {PYTHON_314_MARKER}",
    ]
    assert optional_dependencies["models"] == [
        f"transformers>=5.9; {PYTHON_314_MARKER}",
        f"torch; {PYTHON_314_MARKER}",
        f"accelerate; {PYTHON_314_MARKER}",
        f"timm; {PYTHON_314_MARKER}",
        f"einops; {PYTHON_314_MARKER}",
        f"pillow; {PYTHON_314_MARKER}",
        f"sentencepiece; {PYTHON_314_MARKER}",
        f"qwen-vl-utils; {PYTHON_314_MARKER}",
    ]


def test_dev_dependency_group_includes_review_tooling() -> None:
    """Development metadata includes snapshot and command-mocking helpers."""
    pyproject = _pyproject()
    dev_dependencies = pyproject["dependency-groups"]["dev"]

    assert "cmd-mox>=0.2" in dev_dependencies
    assert "syrupy>=5.3" in dev_dependencies


def test_hecate_policy_models_external_import_names() -> None:
    """Architecture metadata tracks import roots, not distribution names."""
    pyproject = _pyproject()
    hecate_groups = pyproject["tool"]["hecate"]["groups"]
    groups_by_name = {group["name"]: group for group in hecate_groups}

    assert "infrastructure" in groups_by_name["inbound_adapter"]["allowed"]
    assert "PIL" in groups_by_name["infrastructure"]["prefixes"]
    assert "pillow" not in groups_by_name["infrastructure"]["prefixes"]
    assert "cmd_mox" in groups_by_name["infrastructure"]["prefixes"]
    assert "cmdmox" not in groups_by_name["infrastructure"]["prefixes"]
