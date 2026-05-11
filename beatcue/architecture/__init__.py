"""Static architecture checks for BeatCue."""

from __future__ import annotations

from .checker import (
    ArchitectureCheckResult,
    ArchitectureViolation,
    check_architecture,
)
from .policy import fixture_policy

__all__ = [
    "ArchitectureCheckResult",
    "ArchitectureViolation",
    "check_architecture",
    "fixture_policy",
]
