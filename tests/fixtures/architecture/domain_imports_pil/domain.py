"""Fixture package whose domain imports Pillow using the standard PIL root."""

# Pillow is marker-gated on Python 3.14, so this fixture import is intentionally
# unresolved for ty while remaining visible to Hecate.
from PIL import Image  # ruff: ignore[unused-import]  # ty:ignore[unresolved-import]
