"""Fixture domain module that violates the outbound adapter boundary."""

from __future__ import annotations

from .adapters.outbound import StorageAdapter

__all__ = ["StorageAdapter"]
