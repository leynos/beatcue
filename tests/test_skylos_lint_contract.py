"""Contract tests for Skylos dead-code detection in Make and CI.

Skylos accepts scan options before a target path, but its standalone
``whitelist`` subcommand must follow ``skylos`` immediately. It also parses
source through its own Python AST, so the CLI must use Python 3.14. Makeutil
parses the Makefile into structured rules and variables, allowing these tests
to assert that interface without depending on whitespace or source fragments.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess  # noqa: S404 - contract tests invoke fixed local commands.
import tomllib
import typing as typ
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_MAKEUTIL_COMMAND: typ.Final = ("makeutil", "parse", "Makefile")
_MAKEUTIL_REVISION: typ.Final = "29fc5a1634ffbaa18a773eed9dff1b2838a45d9c"
_MAKEUTIL_TOOLCHAIN: typ.Final = "nightly-2026-05-28"
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


def _makefile_report() -> dict[str, object]:
    """Return Makeutil's complete, successfully parsed Makefile report."""
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


def _mapping(value: object, *, subject: str) -> dict[str, object]:
    """Return a JSON object, naming the unexpected subject on failure."""
    assert isinstance(value, dict), f"expected {subject} to be a JSON object"
    return typ.cast("dict[str, object]", value)


def _objects(value: object, *, subject: str) -> list[dict[str, object]]:
    """Return a JSON object array, naming the unexpected subject on failure."""
    assert isinstance(value, list), f"expected {subject} to be a JSON array"
    return [_mapping(item, subject=f"{subject} item") for item in value]


def _text_sequence(value: object, *, subject: str) -> tuple[str, ...]:
    """Return a JSON string array, naming the unexpected subject on failure."""
    assert isinstance(value, list), f"expected {subject} to be a JSON array"
    assert all(isinstance(item, str) for item in value), (
        f"expected {subject} to contain only JSON strings"
    )
    return tuple(typ.cast("list[str]", value))


def _sole_variable(name: str) -> dict[str, object]:
    """Return Makeutil's sole variable fact for a Makefile variable."""
    variables = _objects(_makefile_report().get("variables"), subject="variables")
    matches = [variable for variable in variables if variable.get("name") == name]
    assert len(matches) == 1, (
        f"expected one Makefile variable named {name!r}, found {len(matches)}"
    )
    return matches[0]


def _sole_recipe_rule(target: str) -> dict[str, object]:
    """Return the only parsed rule for a target that has recipes."""
    rules = _objects(_makefile_report().get("rules"), subject="rules")
    matches = [
        rule
        for rule in rules
        if target in _text_sequence(rule.get("targets"), subject="rule targets")
        and _objects(rule.get("recipes"), subject="rule recipes")
    ]
    assert len(matches) == 1, (
        f"expected one recipe-bearing Makefile rule named {target!r}, found "
        f"{len(matches)}"
    )
    return matches[0]


def _variable_tokens(name: str) -> tuple[str, ...]:
    """Return shell-like tokens from a Makeutil raw variable value."""
    value = _sole_variable(name).get("raw_value")
    assert isinstance(value, str), f"expected {name!r} to have a string value"
    return tuple(shlex.split(value))


def _recipe_tokens(target: str) -> tuple[tuple[str, ...], ...]:
    """Return shell-like tokens for every recipe in a Makefile target."""
    recipes = _objects(
        _sole_recipe_rule(target).get("recipes"), subject=f"{target} recipes"
    )
    return tuple(
        tuple(shlex.split(recipe_text))
        for recipe in recipes
        if isinstance(recipe_text := recipe.get("text"), str)
    )


def _workflow_job(workflow_path: str, job_name: str) -> dict[str, object]:
    """Return the named job from a repository workflow."""
    workflow = yaml.safe_load(
        (REPOSITORY_ROOT / workflow_path).read_text(encoding="utf-8")
    )
    workflow_mapping = _mapping(workflow, subject=f"{workflow_path} workflow")
    jobs = _mapping(workflow_mapping.get("jobs"), subject=f"{workflow_path} jobs")
    return _mapping(jobs.get(job_name), subject=f"{workflow_path} job {job_name!r}")


def _sole_workflow_step(job_name: str, step_name: str) -> dict[str, object]:
    """Return the sole named CI step from a job in the main workflow."""
    job = _workflow_job(".github/workflows/ci.yml", job_name)
    steps = _objects(job.get("steps"), subject=f"{job_name!r} job steps")
    matches = [step for step in steps if step.get("name") == step_name]
    assert len(matches) == 1, (
        f"expected one {step_name!r} step in {job_name!r}, found {len(matches)}"
    )
    return matches[0]


def _run_skylos_allow(*arguments: str) -> subprocess.CompletedProcess[str]:
    """Run the non-mutating whitelist boundary with a WSL-like environment."""
    environment = {**os.environ, "NAME": "wsl-hostname"}
    environment.pop("REASON", None)
    environment.pop("SYMBOL", None)
    return subprocess.run(  # noqa: S603 - fixed Make target and arguments.
        (_make_executable(), "skylos-allow", *arguments),
        capture_output=True,
        check=False,
        cwd=REPOSITORY_ROOT,
        env=environment,
        text=True,
    )


def _make_executable() -> str:
    """Return the absolute Make executable used by subprocess boundaries."""
    executable = shutil.which("make")
    assert executable is not None, "Skylos contract tests require make on PATH"
    return executable


def _assert_makeutil_installation(command: object, *, contract: str) -> None:
    """Assert that a workflow command installs the pinned Makeutil parser."""
    assert isinstance(command, str), (
        f"{contract} must provide a Makeutil installation shell command"
    )
    assert (
        tuple(shlex.split(command.replace("\\\n", ""))) == _MAKEUTIL_INSTALL_TOKENS
    ), f"{contract} must pin the Makeutil installation command"


def test_lint_recipe_runs_the_production_dead_code_gate() -> None:
    """The lint gate must scan only production dead code with Skylos."""
    assert _variable_tokens("SKYLOS_VERSION") == ("4.33.2",), (
        "Skylos version contract must pin 4.33.2"
    )
    assert _variable_tokens("SKYLOS_PRODUCTION_TARGETS") == ("beatcue",), (
        "Skylos production-target contract must scan beatcue"
    )
    assert _variable_tokens("SKYLOS_EXCLUDE_FOLDERS") == ("tests",), (
        "Skylos exclusion contract must omit tests"
    )
    skylos_commands = [
        command for command in _recipe_tokens("lint") if command[:1] == ("$(SKYLOS)",)
    ]

    assert skylos_commands == [
        (
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
    ], "Skylos lint command contract must scan production dead code strictly"


def test_whitelist_target_uses_skylos_subcommand_contract() -> None:
    """The whitelist subcommand must precede its arguments and scan options."""
    assert _variable_tokens("SKYLOS_CLI") == (
        "$(UV_ENV)",
        "$(UV)",
        "tool",
        "run",
        "--python",
        "3.14",
        "--from",
        "skylos==$(SKYLOS_VERSION)",
        "skylos",
    ), "Skylos CLI contract must pin Python 3.14 and its tool release"
    assert _variable_tokens("SKYLOS") == (
        "$(SKYLOS_CLI)",
        "--config-file",
        "pyproject.toml",
    ), "Skylos scan command contract must add only the configuration file"

    whitelist_commands = [
        command
        for command in _recipe_tokens("skylos-allow")
        if command[:1] == ("$(SKYLOS_CLI)",)
    ]
    assert whitelist_commands == [
        (
            "$(SKYLOS_CLI)",
            "whitelist",
            "$${SKYLOS_SYMBOL}",
            "--reason",
            "$${SKYLOS_REASON}",
        )
    ], "Skylos whitelist command contract must dispatch before --reason"


def test_skylos_allow_requires_symbol_and_reason() -> None:
    """The whitelist target must reject incomplete input without running Skylos."""
    for arguments, expected_error in (
        ((), "Error: SYMBOL is required for a named whitelist exception"),
        (
            ("SYMBOL=handler",),
            "Error: REASON is required for a named whitelist exception",
        ),
    ):
        completed = _run_skylos_allow(*arguments)

        assert completed.returncode == 2, (
            "Skylos whitelist boundary must reject missing required arguments"
        )
        assert expected_error in completed.stderr, (
            "Skylos whitelist boundary must name the missing required argument"
        )


def test_skylos_allow_dry_run_preserves_the_whitelist_command_contract() -> None:
    """A valid dry run must reveal the command without writing an exception."""
    completed = subprocess.run(  # noqa: S603 - fixed dry-run contract command.
        (
            _make_executable(),
            "--dry-run",
            "skylos-allow",
            "SYMBOL=handler",
            "REASON=Loaded by plugin registry",
        ),
        capture_output=True,
        check=False,
        cwd=REPOSITORY_ROOT,
        text=True,
    )

    assert completed.returncode == 0, (
        "Skylos whitelist dry-run contract must accept complete input"
    )
    assert (
        'skylos whitelist "${SKYLOS_SYMBOL}" --reason "${SKYLOS_REASON}"'
        in completed.stdout
    ), "Skylos whitelist dry-run contract must preserve subcommand argument order"


def test_skylos_configuration_enables_the_strict_gate() -> None:
    """Skylos configuration must preserve strict dead-code gate behaviour."""
    with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as configuration_file:
        configuration = tomllib.load(configuration_file)

    tool = _mapping(configuration.get("tool"), subject="tool configuration")
    skylos = _mapping(tool.get("skylos"), subject="Skylos configuration")
    gate = _mapping(skylos.get("gate"), subject="Skylos gate configuration")

    assert gate.get("strict") is True, (
        "Skylos gate configuration must enable strict mode"
    )


def test_ci_runs_the_shared_lint_target_and_installs_makeutil() -> None:
    """The full-suite CI job must run lint and install the pinned parser."""
    lint_step = _sole_workflow_step(
        "lint-test", "Run lint, including Skylos dead-code detection"
    )
    assert lint_step.get("run") == "make lint", (
        "CI lint-step contract must invoke the shared make lint target"
    )

    coverage_job = _workflow_job(".github/workflows/ci.yml", "lint-test")
    environment = _mapping(
        coverage_job.get("env"), subject="CI full-suite Makeutil environment"
    )
    assert environment.get("MAKEUTIL_REVISION") == _MAKEUTIL_REVISION, (
        "CI full-suite Makeutil revision contract must stay pinned"
    )
    assert environment.get("MAKEUTIL_TOOLCHAIN") == _MAKEUTIL_TOOLCHAIN, (
        "CI full-suite Makeutil toolchain contract must stay pinned"
    )
    parser_step = _sole_workflow_step("lint-test", "Install Makefile parser")
    _assert_makeutil_installation(
        parser_step.get("run"), contract="CI full-suite Makeutil-install contract"
    )
