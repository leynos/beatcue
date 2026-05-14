"""Command-line interface for BeatCue architecture checks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .checker import check_architecture
from .policy import fixture_policy


def _build_parser() -> argparse.ArgumentParser:
    """Build the architecture-checker argument parser."""
    parser = argparse.ArgumentParser(
        description="Check BeatCue hexagonal import boundaries.",
    )
    parser.add_argument(
        "--package",
        default="beatcue",
        help="Dotted package name to check.",
    )
    parser.add_argument(
        "--root",
        default="beatcue",
        help="Filesystem root for the checked package.",
    )
    parser.add_argument(
        "--fixture-policy",
        action="store_true",
        help="Use the generic test fixture policy.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the architecture checker and return a process exit code.

    Parameters
    ----------
    argv
        Command-line arguments. When None, ``argparse`` reads ``sys.argv[1:]``.

    Returns
    -------
    int
        Exit code: ``0`` when all architecture boundaries pass, ``1`` for
        boundary violations, and ``2`` for invalid checker inputs.

    """
    args = _build_parser().parse_args(argv)
    policy = fixture_policy(args.package) if args.fixture_policy else None
    try:
        result = check_architecture(
            package_root=Path(args.root),
            package=args.package,
            policy=policy,
        )
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for violation in result.violations:
        print(violation.render(), file=sys.stderr)
    return 0 if result.ok else 1
