"""Fixture adapter package barrel with a star re-export."""

from __future__ import annotations

from .outbound import *  # noqa: F403 - intentional star re-export for public API

__all__ = ["StorageAdapter"]  # noqa: F405 - explicit public API symbol
