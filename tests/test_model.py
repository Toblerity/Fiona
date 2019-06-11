"""Test of deprecations following RFC 1"""

import pytest

from fiona.errors import FionaDeprecationWarning
from fiona.model import Object


def test_object_len():
    """object len is correct"""
    obj = Object(g=1)
    assert len(obj) == 1


def test_object_iter():
    """object iter is correct"""
    obj = Object(g=1)
    assert [obj[k] for k in obj] == [1]


def test_setitem_warning():
    """Warn about __setitem__"""
    obj = Object()
    with pytest.warns(FionaDeprecationWarning, match="immutable"):
        obj["g"] = 1
    assert "g" in obj
    assert obj["g"] == 1


def test_delitem_warning():
    """Warn about __delitem__"""
    obj = Object(g=1)
    with pytest.warns(FionaDeprecationWarning, match="immutable"):
        del obj["g"]
    assert "g" not in obj
