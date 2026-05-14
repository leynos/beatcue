"""Tests for BeatCue architecture re-export resolution."""

from __future__ import annotations

import keyword
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from beatcue.architecture.reexports import build_reexport_index

_SYMBOL_NAME = st.from_regex(r"[A-Z][A-Za-z0-9_]{0,20}", fullmatch=True).filter(
    lambda value: not keyword.iskeyword(value)
)


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


def test_reexport_index_uses_fallback_when_final_all_assignment_is_unresolved(
    tmp_path: Path,
) -> None:
    """A final unresolved ``__all__`` falls back to discovered public symbols."""
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
            "__all__ = ['FirstExport']",
            "__all__: list[str]",
        ]),
        encoding="utf-8",
    )

    result = build_reexport_index(package_root, "sample")

    assert result == {
        "sample.FirstExport": "sample.module.FirstExport",
        "sample.LastExport": "sample.module.LastExport",
    }


@given(symbol_name=_SYMBOL_NAME)
def test_reexport_index_is_idempotent_for_static_packages(symbol_name: str) -> None:
    """Re-export indexing is stable for unchanged package contents."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        package_root = Path(tmp_dir) / "sample"
        package_root.mkdir()
        (package_root / "__init__.py").write_text(
            "from .module import *\n",
            encoding="utf-8",
        )
        (package_root / "module.py").write_text(
            "\n".join([
                f"class {symbol_name}: ...",
                f"__all__ = ['{symbol_name}']",
            ]),
            encoding="utf-8",
        )

        first_result = build_reexport_index(package_root, "sample")
        second_result = build_reexport_index(package_root, "sample")

    assert first_result == second_result
    assert first_result == {f"sample.{symbol_name}": f"sample.module.{symbol_name}"}
