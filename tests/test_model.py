"""Test of deprecations following RFC 1"""

import pytest

from fiona.errors import FionaDeprecationWarning
from fiona.model import Feature, Geometry, Object


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


def test_update_warning():
    """Warn about update"""
    obj = Object()
    with pytest.warns(FionaDeprecationWarning, match="immutable"):
        obj.update(g=1)
    assert "g" in obj
    assert obj["g"] == 1


def test_popitem_warning():
    """Warn about pop"""
    obj = Object(g=1)
    with pytest.warns(FionaDeprecationWarning, match="immutable"):
        assert obj.pop("g") == 1
    assert "g" not in obj


def test_delitem_warning():
    """Warn about __delitem__"""
    obj = Object(g=1)
    with pytest.warns(FionaDeprecationWarning, match="immutable"):
        del obj["g"]
    assert "g" not in obj


def test_geometry_type():
    """Geometry has a type"""
    geom = Geometry(type="Point")
    assert geom.type == "Point"


def test_geometry_coordinates():
    """Geometry has coordinates"""
    geom = Geometry(coordinates=[(0, 0), (1, 1)])
    assert geom.coordinates == [(0, 0), (1, 1)]


def test_feature_no_geometry():
    """Feature has no attribute"""
    feat = Feature()
    assert feat.geometry == Object()


def test_feature_geometry():
    """Feature has a geometry attribute"""
    feat = Feature(geometry={"type": "Point"})
    assert feat.geometry is not None


def test_feature_no_id():
    """Feature has no id"""
    feat = Feature()
    assert feat.id is None


def test_feature_id():
    """Feature has an id"""
    feat = Feature(id="123")
    assert feat.id == "123"


def test_feature_no_properties():
    """Feature has no properties"""
    feat = Feature()
    assert feat.properties == Object()


def test_feature_properties():
    """Feature has properties"""
    feat = Feature(properties={"foo": 1})
    assert len(feat.properties) == 1
    assert feat.properties["foo"] == 1


def test_feature_complete():
    """Feature can be created from GeoJSON"""
    data = {
        "id": "foo",
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": (0, 0)},
        "properties": {"a": 0, "b": "bar"},
        "extras": {"this": 1}
    }
    feat = Feature(**data)
    assert feat.id == "foo"
    assert feat.type == "Feature"
    assert feat.geometry.type == "Point"
    assert feat.geometry.coordinates == (0, 0)
    assert len(feat.properties) == 2
    assert feat.properties["a"] == 0
    assert feat.properties["b"] == "bar"
    assert feat["extras"]["this"] == 1
