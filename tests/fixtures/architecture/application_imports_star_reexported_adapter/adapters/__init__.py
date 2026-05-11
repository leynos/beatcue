"""Fixture adapter package barrel with a star re-export."""

from __future__ import annotations

from .outbound import *  # noqa: F403

__all__ = ["StorageAdapter"]  # noqa: F405
