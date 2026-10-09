"""Tests for the repository spelling-policy scripts."""

from __future__ import annotations

import ast
import importlib
import os
import tomllib
import typing as typ
import urllib.error
from pathlib import Path

import pytest

if typ.TYPE_CHECKING:
    import types

SCRIPT_DIRECTORY = Path(__file__).resolve().parents[1]


def test_rollout_scripts_support_python_313() -> None:
    """Every rollout script parses with the declared minimum Python version."""
    for script in SCRIPT_DIRECTORY.glob("*.py"):
        ast.parse(
            script.read_text(encoding="utf-8"),
            filename=str(script),
            feature_version=(3, 13),
        )


@pytest.fixture(name="rollout_modules")
def rollout_modules_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[types.ModuleType, types.ModuleType, types.ModuleType]:
    """Import the scripts through the same top-level module path used at runtime."""
    monkeypatch.syspath_prepend(str(SCRIPT_DIRECTORY))
    names = ("typos_rollout_cache", "typos_rollout", "generate_typos_config")
    importlib.invalidate_caches()
    cache, rollout, generator = (importlib.import_module(name) for name in names)
    return cache, rollout, generator


def _dictionary_text(stem: str = "organ") -> str:
    """Return a minimal valid shared-dictionary document."""
    return (
        'schema = 1\n\n[oxford]\nstems = ["'
        + stem
        + '"]\n\n[words]\naccepted = []\n\n[words.corrections]\n\n'
        + "[patterns]\nignore = []\n\n[files]\nexclude = []\n"
    )


def test_rollout_generates_oxford_corrections(
    rollout_modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
) -> None:
    """The shared renderer accepts Oxford forms and corrects plain-British ones."""
    _, rollout, _ = rollout_modules

    mappings = rollout.generate_word_mappings(rollout.Dictionary(stems=("organ",)))

    assert mappings["organize"] == "organize"
    assert mappings["organise"] == "organize"


def test_local_refresh_keeps_a_newer_cache(
    rollout_modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    tmp_path: Path,
) -> None:
    """An older local authority cannot replace a newer untracked cache."""
    _, rollout, _ = rollout_modules
    source = tmp_path / "shared.toml"
    cache = tmp_path / ".typos-base.toml"
    metadata = tmp_path / ".typos-base.json"
    source.write_text(_dictionary_text(), encoding="utf-8")
    source.touch()
    rollout.refresh_base(source, cache, metadata=metadata)
    cache.write_text(_dictionary_text("newer"), encoding="utf-8")
    cache.touch()
    source_mtime = source.stat().st_mtime_ns
    cache_mtime = max(cache.stat().st_mtime_ns, source_mtime + 1)
    os.utime(cache, ns=(cache_mtime, cache_mtime))

    result = rollout.refresh_base(source, cache, metadata=metadata)

    assert result.status == "current"
    assert rollout.load_dictionary(cache).stems == ("newer",)


def test_https_failure_reuses_valid_tracked_config(
    rollout_modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A clean network-restricted checkout retains its reviewed policy."""
    _, rollout, generator = rollout_modules
    tracked_config = tmp_path / "typos.toml"
    tracked_config.write_text('[default]\nlocale = "en-gb"\n', encoding="utf-8")
    offline_message = "offline"

    def unavailable(*_args: object, **_kwargs: object) -> None:
        """Model an unavailable HTTPS authority."""
        raise urllib.error.URLError(offline_message)

    monkeypatch.setattr(rollout, "refresh_base", unavailable)

    result = generator.main(repository=tmp_path, source="https://example.invalid/base")

    assert result.status == "tracked-config"
    assert result.cache == tracked_config


def test_local_policy_preserves_committed_inline_code_exemptions(
    rollout_modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
    tmp_path: Path,
) -> None:
    """The generated configuration retains the committed inline-code policy."""
    _, _, generator = rollout_modules
    (tmp_path / ".typos-oxendict-base.toml").write_text(
        _dictionary_text(), encoding="utf-8"
    )
    committed_policy_path = SCRIPT_DIRECTORY.parent / "typos.local.toml"
    committed_policy_text = committed_policy_path.read_text(encoding="utf-8")
    committed_policy = tomllib.loads(committed_policy_text)
    (tmp_path / "typos.local.toml").write_text(
        committed_policy_text,
        encoding="utf-8",
    )

    configuration = tomllib.loads(generator.render_config(tmp_path))
    expected_patterns = committed_policy["patterns"]["ignore"]
    generated_patterns = configuration["default"]["extend-ignore-re"]

    assert set(expected_patterns) <= set(generated_patterns), (
        "generated configuration must retain the committed spelling policy"
    )
    assert "`[^`\\n]+`" not in generated_patterns, (
        "generated configuration must not restore a blanket inline-code exemption"
    )


def _render_committed_spelling_policy(
    rollout: types.ModuleType,
    committed_path: Path,
) -> tuple[str, list[str], dict[str, str]]:
    """Render the committed policy and return its exclusions and word entries."""
    committed = tomllib.loads(committed_path.read_text(encoding="utf-8"))
    committed_files = typ.cast("dict[str, object]", committed["files"])
    committed_default = typ.cast("dict[str, object]", committed["default"])
    committed_exclusions = typ.cast("list[str]", committed_files["extend-exclude"])
    committed_patterns = typ.cast("list[str]", committed_default["extend-ignore-re"])
    committed_words = typ.cast("dict[str, str]", committed_default["extend-words"])
    dictionary = rollout.Dictionary(
        accepted=tuple(
            word for word, correction in committed_words.items() if word == correction
        ),
        corrections=tuple(
            (word, correction)
            for word, correction in committed_words.items()
            if word != correction
        ),
        ignore_patterns=tuple(committed_patterns),
        excluded_files=tuple(committed_exclusions),
    )
    return (
        rollout.render_typos_config(dictionary),
        committed_exclusions,
        committed_words,
    )


def test_generated_exclusions_and_words_match_committed_policy(
    rollout_modules: tuple[types.ModuleType, types.ModuleType, types.ModuleType],
) -> None:
    """The renderer must preserve committed exclusions and generated word entries."""
    _, rollout, _ = rollout_modules
    committed_path = SCRIPT_DIRECTORY.parent / "typos.toml"
    rendered, committed_exclusions, committed_words = _render_committed_spelling_policy(
        rollout,
        committed_path,
    )
    generated = tomllib.loads(rendered)
    generated_files = typ.cast("dict[str, object]", generated["files"])
    generated_default = typ.cast("dict[str, object]", generated["default"])

    assert generated_files["extend-exclude"] == committed_exclusions, (
        "generated spelling configuration must retain committed file exclusions"
    )
    assert generated_default["extend-words"] == committed_words, (
        "generated spelling configuration must retain committed word entries"
    )
