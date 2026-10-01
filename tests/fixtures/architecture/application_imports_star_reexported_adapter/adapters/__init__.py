"""Fixture adapter package barrel with a star re-export."""

from __future__ import annotations

from .outbound import *  # ruff: ignore[undefined-local-with-import-star] - intentional star re-export for public API

__all__ = ["StorageAdapter"]  # ruff: ignore[undefined-local-with-import-star-usage] - explicit public API symbol
