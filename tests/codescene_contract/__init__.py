"""Readers and rules for the CV-005 CodeScene coverage contract.

The judgements live here, apart from the tests, so the fixture cases can drive
each rule against breaching documents directly: a rule exercised only over this
repository's own correct workflows would pass whether or not it detects
anything. ``tests/test_codescene_contract.py`` then applies the same functions
to the real files.
"""
