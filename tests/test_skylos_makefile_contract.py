"""Structured Makefile and CI contracts for the Skylos lint gate."""

from __future__ import annotations

import json
import shlex
import subprocess  # noqa: S404 - contract test invokes the fixed parser.
import typing as typ
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_MAKEUTIL_COMMAND: typ.Final = ("makeutil", "parse", "Makefile")
_MAKEUTIL_REVISION: typ.Final = "29fc5a1634ffbaa18a773eed9dff1b2838a45d9c"
_MAKEUTIL_TOOLCHAIN: typ.Final = "nightly-2026-05-28"
_FULL_SUITE_WORKFLOWS: typ.Final = (
    (".github/workflows/ci.yml", "lint-test"),
    (".github/workflows/coverage-main.yml", "coverage-upload"),
)
_EXPECTED_LINT_STEP_NAME: typ.Final = "Run lint gates"
_EXPECTED_MAKEUTIL_PREREQUISITE: typ.Final = "makeutil"
_EXPECTED_MAKEUTIL_GUARD: typ.Final = "$(call ensure_tool,$@)"
_EXPECTED_SKYLOS_VERSION: typ.Final = ("4.33.2",)
_EXPECTED_SKYLOS_CLI: typ.Final = (
    "$(UV_ENV)",
    "$(UV)",
    "tool",
    "run",
    "--python",
    "3.14",
    "--from",
    "skylos==$(SKYLOS_VERSION)",
    "skylos",
)
_EXPECTED_SKYLOS_SCAN: typ.Final = (
    "$(SKYLOS_CLI)",
    "--config-file",
    "pyproject.toml",
)
_EXPECTED_PRODUCTION_TARGETS: typ.Final = ("beatcue",)
_EXPECTED_EXCLUDE_FOLDERS: typ.Final = ("tests",)
_EXPECTED_ALLOW_LOCK: typ.Final = (".skylos/skylos-allow.lock",)
_EXPECTED_LINT_COMMAND: typ.Final = (
    "$(SKYLOS)",
    "$(SKYLOS_PRODUCTION_TARGETS)",
    "--exclude",
    "$(SKYLOS_EXCLUDE_FOLDERS)",
    "--category",
    "dead_code",
    "--gate",
    "--format",
    "concise",
    "--no-upload",
    "--no-provenance",
    "--no-grep-verify",
)
_EXPECTED_WHITELIST_COMMAND: typ.Final = (
    "flock",
    "$(SKYLOS_ALLOW_LOCK)",
    "env",
    "$(SKYLOS_CLI)",
    "whitelist",
    "$${SKYLOS_SYMBOL}",
    "--reason",
    "$${SKYLOS_REASON}",
)
_MAKEUTIL_INSTALL_TOKENS: typ.Final = (
    "rustup",
    "toolchain",
    "install",
    "${MAKEUTIL_TOOLCHAIN}",
    "--profile",
    "minimal",
    "RUSTFLAGS=-Zpolonius=next",
    "cargo",
    "+${MAKEUTIL_TOOLCHAIN}",
    "install",
    "--git",
    "https://github.com/leynos/makeutil",
    "--rev",
    "${MAKEUTIL_REVISION}",
    "--locked",
    "--force",
    "makeutil",
)


def _mapping(value: object, *, subject: str) -> dict[str, object]:
    """Return a JSON object or name the unexpected contract subject."""
    assert isinstance(value, dict), f"expected {subject} to be a JSON object"
    return typ.cast("dict[str, object]", value)


def _objects(value: object, *, subject: str) -> list[dict[str, object]]:
    """Return a JSON object array or name the unexpected contract subject."""
    assert isinstance(value, list), f"expected {subject} to be a JSON array"
    return [_mapping(item, subject=f"{subject} item") for item in value]


def _text_sequence(value: object, *, subject: str) -> tuple[str, ...]:
    """Return a JSON string array or name the unexpected contract subject."""
    assert isinstance(value, list), f"expected {subject} to be a JSON array"
    assert all(isinstance(item, str) for item in value), (
        f"expected {subject} to contain only JSON strings"
    )
    return tuple(typ.cast("list[str]", value))


def _makefile_report() -> dict[str, object]:
    """Return Makeutil's complete parsed report without caching it between tests."""
    completed = subprocess.run(  # noqa: S603 - fixed parser command.
        _MAKEUTIL_COMMAND,
        capture_output=True,
        check=True,
        cwd=REPOSITORY_ROOT,
        text=True,
    )
    report = typ.cast("dict[str, object]", json.loads(completed.stdout))
    parse = _mapping(report.get("parse"), subject="parse report")
    assert parse.get("status") == "complete", (
        f"makeutil did not complete the Makefile parse: {parse!r}"
    )
    return report


def _variable_tokens(name: str) -> tuple[str, ...]:
    """Return shell tokens from the sole named Makefile variable."""
    variables = _objects(_makefile_report().get("variables"), subject="variables")
    matches = [variable for variable in variables if variable.get("name") == name]
    assert len(matches) == 1, (
        f"expected one Makefile variable named {name!r}, found {len(matches)}"
    )
    value = matches[0].get("raw_value")
    assert isinstance(value, str), f"expected {name!r} to have a string value"
    return tuple(shlex.split(value))


def _recipe_commands(target: str, command: str) -> list[tuple[str, ...]]:
    """Return parsed recipes for a target beginning with the named command."""
    rules = _objects(_makefile_report().get("rules"), subject="rules")
    recipes = [
        recipe
        for rule in rules
        if target in _text_sequence(rule.get("targets"), subject="rule targets")
        for recipe in _objects(rule.get("recipes"), subject="rule recipes")
    ]
    recipe_tokens = [
        tuple(shlex.split(text))
        for recipe in recipes
        if isinstance(text := recipe.get("text"), str)
    ]
    return [tokens for tokens in recipe_tokens if tokens[:1] == (command,)]


def _rule_for(target: str) -> dict[str, object]:
    """Return the sole parsed Makefile rule that declares a target."""
    rules = _objects(_makefile_report().get("rules"), subject="rules")
    matches = [
        rule
        for rule in rules
        if target in _text_sequence(rule.get("targets"), subject="rule targets")
    ]
    assert len(matches) == 1, (
        f"expected one parsed Makefile rule for {target!r}, found {len(matches)}"
    )
    return matches[0]


def _workflow_job(workflow_path: str, job_name: str) -> dict[str, object]:
    """Return the named job from a committed workflow."""
    workflow = yaml.safe_load(
        (REPOSITORY_ROOT / workflow_path).read_text(encoding="utf-8")
    )
    jobs = _mapping(
        _mapping(workflow, subject=f"{workflow_path} workflow").get("jobs"),
        subject=f"{workflow_path} jobs",
    )
    return _mapping(jobs.get(job_name), subject=f"{workflow_path} job {job_name!r}")


def _assert_makeutil_installation(workflow_path: str, job_name: str) -> None:
    """Assert that a full-suite job independently installs pinned Makeutil."""
    contract = f"{workflow_path} full-suite Makeutil"
    job = _workflow_job(workflow_path, job_name)
    environment = _mapping(job.get("env"), subject=f"{contract} environment")
    assert environment.get("MAKEUTIL_REVISION") == _MAKEUTIL_REVISION, (
        f"{contract} revision contract must stay pinned"
    )
    assert environment.get("MAKEUTIL_TOOLCHAIN") == _MAKEUTIL_TOOLCHAIN, (
        f"{contract} toolchain contract must stay pinned"
    )
    steps = _objects(job.get("steps"), subject=f"{contract} steps")
    parser_steps = [
        step for step in steps if step.get("name") == "Install Makefile parser"
    ]
    assert len(parser_steps) == 1, (
        f"{contract} must contain one Makeutil installation step"
    )
    command = parser_steps[0].get("run")
    assert isinstance(command, str), (
        f"{contract} installation step must provide a shell command"
    )
    assert (
        tuple(shlex.split(command.replace("\\\n", ""))) == _MAKEUTIL_INSTALL_TOKENS
    ), f"{contract} must pin the Makeutil installation command"


def test_makefile_preserves_the_strict_production_skylos_contract() -> None:
    """The structured Makefile must pin the complete Skylos gate interface."""
    assert _variable_tokens("SKYLOS_VERSION") == _EXPECTED_SKYLOS_VERSION, (
        "Skylos version contract must pin 4.33.2"
    )
    assert _variable_tokens("SKYLOS_CLI") == _EXPECTED_SKYLOS_CLI, (
        "Skylos CLI contract must pin Python 3.14 and its tool release"
    )
    assert _variable_tokens("SKYLOS") == _EXPECTED_SKYLOS_SCAN, (
        "Skylos scan command contract must add only the configuration file"
    )
    assert (
        _variable_tokens("SKYLOS_PRODUCTION_TARGETS") == _EXPECTED_PRODUCTION_TARGETS
    ), "Skylos production-target contract must scan beatcue"
    assert _variable_tokens("SKYLOS_EXCLUDE_FOLDERS") == _EXPECTED_EXCLUDE_FOLDERS, (
        "Skylos exclusion contract must omit tests"
    )
    assert _variable_tokens("SKYLOS_ALLOW_LOCK") == _EXPECTED_ALLOW_LOCK, (
        "Skylos whitelist lock contract must use the ignored local lock file"
    )
    assert _recipe_commands("lint", "$(SKYLOS)") == [_EXPECTED_LINT_COMMAND], (
        "Skylos lint command contract must scan production dead code strictly"
    )
    assert _recipe_commands("skylos-allow", "flock") == [_EXPECTED_WHITELIST_COMMAND], (
        "Skylos whitelist contract must serialize command-first forwarding"
    )


def test_make_test_requires_a_present_makefile_parser() -> None:
    """The full pytest target must verify Makeutil before running tests."""
    test_rule = _rule_for("test")
    prerequisites = _text_sequence(
        test_rule.get("prerequisites"), subject="test prerequisites"
    )
    assert _EXPECTED_MAKEUTIL_PREREQUISITE in prerequisites, (
        "make test must require the Makeutil binary"
    )

    makeutil_rule = _rule_for(_EXPECTED_MAKEUTIL_PREREQUISITE)
    recipes = _objects(makeutil_rule.get("recipes"), subject="makeutil recipes")
    assert tuple(recipe.get("text") for recipe in recipes) == (
        _EXPECTED_MAKEUTIL_GUARD,
    ), "makeutil target must use the shared binary-presence check"


def test_each_full_suite_workflow_installs_the_pinned_makefile_parser() -> None:
    """Every full-suite CI lane provisions its own Makeutil binary."""
    for workflow_path, job_name in _FULL_SUITE_WORKFLOWS:
        _assert_makeutil_installation(workflow_path, job_name)


def test_ci_runs_the_shared_lint_target() -> None:
    """The pull-request CI job runs the shared lint target."""
    job = _workflow_job(".github/workflows/ci.yml", "lint-test")
    steps = _objects(job.get("steps"), subject="CI full-suite steps")
    lint_steps = [
        step for step in steps if step.get("name") == _EXPECTED_LINT_STEP_NAME
    ]
    assert len(lint_steps) == 1, (
        "pull-request CI must contain one shared lint-gate step"
    )
    assert lint_steps[0].get("run") == "make lint", (
        "pull-request CI lint-step contract must invoke the shared make lint target"
    )
