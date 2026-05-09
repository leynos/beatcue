"""Smoke tests for the public BeatCue package API."""

from __future__ import annotations

import beatcue


def test_hello_uses_available_implementation() -> None:
    """The package root re-exports the configured hello implementation."""
    assert beatcue.hello() == "hello from Python", (
        "Expected beatcue.hello() to return the Python smoke-check greeting"
    )
