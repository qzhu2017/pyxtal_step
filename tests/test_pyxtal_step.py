#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `pyxtal_step` package."""

import pytest  # noqa: F401
import pyxtal_step  # noqa: F401


def test_construction():
    """Just create an object and test its type."""
    result = pyxtal_step.PyXtal()
    assert str(type(result)) == "<class 'pyxtal_step.pyxtal.PyXtal'>"
