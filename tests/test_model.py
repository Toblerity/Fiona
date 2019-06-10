"""Test of deprecations following RFC 1"""

import pytest

from fiona.errors import FionaDeprecationWarning
from fiona.model import Object


def test_setitem_warning():
    """Warn about __setitem__"""
    obj = Object()
    with pytest.warns(FionaDeprecationWarning):
        obj['g'] = 1
    assert obj['g'] == 1


def test_delitem_warning():
    """Warn about __delitem__"""
    obj = Object(g=1)
    with pytest.warns(FionaDeprecationWarning):
        del obj['g']
    assert 'g' not in obj
