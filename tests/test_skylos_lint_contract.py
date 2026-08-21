"""Contract tests for the blocking Skylos dead-code lint gate."""

import shutil
import subprocess  # noqa: S404 - contract test executes make without a shell
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_make_lint_runs_production_only_skylos_scan() -> None:
    """Keep the Skylos command deterministic and scoped to production code."""
    make_executable = shutil.which("make")
    assert make_executable is not None, "Expected make to be available for the test."

    result = subprocess.run(  # noqa: S603 - contract test executes make without a shell
        [make_executable, "--no-print-directory", "--dry-run", "lint"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, "Expected the lint dry run to succeed."
    expected_command = (
        "skylos --config-file pyproject.toml beatcue --category dead_code --gate "
        "--format concise --no-upload --no-provenance --no-grep-verify"
    )
    assert expected_command in result.stdout, (
        "Expected make lint to run one blocking Skylos production scan."
    )
