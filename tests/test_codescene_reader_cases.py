"""Drive the workflow reader's boundary against a scratch directory.

Every failure to list or read a workflow must surface as ``WorkflowError``
naming the path: a bare ``OSError`` or ``UnicodeDecodeError`` escapes the
contract's own error type, and an empty directory would let every clause pass
having read nothing.
"""

from __future__ import annotations

import typing as typ

import pytest
from codescene_contract import reader

if typ.TYPE_CHECKING:
    from pathlib import Path


def test_a_missing_directory_is_a_reading_error(tmp_path: Path) -> None:
    """A workflow directory that is not there cannot be listed."""
    with pytest.raises(reader.WorkflowError, match="cannot list"):
        reader.workflows(tmp_path / "absent")


def test_an_empty_directory_is_a_reading_error(tmp_path: Path) -> None:
    """A directory holding no workflow gives every clause nothing to read."""
    with pytest.raises(reader.WorkflowError, match="no workflows found"):
        reader.workflows(tmp_path)


def test_an_undecodable_workflow_is_a_reading_error(tmp_path: Path) -> None:
    """A workflow that is not UTF-8 is named, not raised as a decode error."""
    (tmp_path / "bad.yml").write_bytes(b"\xff\xfe on: push\n")
    with pytest.raises(reader.WorkflowError, match="cannot read"):
        reader.workflows(tmp_path)
