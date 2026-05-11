"""Fixture composition root that wires concrete adapters."""

from __future__ import annotations

from .adapters.outbound import StorageAdapter
from .application import AnalyseVideo

__all__ = ["AnalyseVideo", "StorageAdapter"]
