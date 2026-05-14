"""Fixture inbound CLI adapter that violates outbound adapter wiring."""

from __future__ import annotations

from .adapters.outbound import StorageAdapter

__all__ = ["StorageAdapter"]
