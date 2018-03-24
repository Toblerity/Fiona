import pytest
import fiona
import binascii
from six import integer_types, string_types
try:
    from fiona._vectorized import read_vectorized
except ImportError:
    pytestmark = pytest.mark.skip
else:
    import numpy as np
    from numpy.testing import assert_allclose
from .conftest import requires_gpkg
from .test_binary_field import write_binary_gpkg

def test_read_vectorized(path_coutwildrnp_shp):
    with fiona.open(path_coutwildrnp_shp, "r") as collection:
        features = read_vectorized(collection)
    
        assert len(features["geometry"]) == 67
        assert features["geometry"].dtype == object
        assert features["geometry"][0].decode("ascii").startswith("POLYGON (")
        assert features["geometry"][-1].decode("ascii").startswith("POLYGON (")
        # TODO: better checks for geometry
        
        # check number of properties
        assert len(features["properties"]) == len(collection.schema["properties"])

        # float
        assert features["properties"]["PERIMETER"].dtype == np.float64
        assert features["properties"]["PERIMETER"].shape == (67,)
        assert_allclose(features["properties"]["PERIMETER"][0], 1.22107)
        assert_allclose(features["properties"]["PERIMETER"][-1], 0.120627)
        
        # integer
        assert features["properties"]["WILDRNP020"].dtype == np.int64
        assert features["properties"]["WILDRNP020"].shape == (67,)
        assert features["properties"]["WILDRNP020"][0] == 332
        assert features["properties"]["WILDRNP020"][-1] == 511
        
        # string
        assert isinstance(features["properties"]["NAME"].dtype, object)
        assert features["properties"]["NAME"].shape == (67,)
        assert features["properties"]["NAME"][0] == "Mount Naomi Wilderness"
        assert features["properties"]["NAME"][-1] == "Mesa Verde Wilderness"

def test_ignore_fields(path_coutwildrnp_shp):
    with fiona.open(path_coutwildrnp_shp, ignore_fields=["NAME"]) as collection:
        features = read_vectorized(collection)

        assert "PERIMETER" in features["properties"]
        assert "WILDRNP020" in features["properties"]
        assert "NAME" not in features["properties"]

        assert features["geometry"] is not None

def test_ignore_geometry(path_coutwildrnp_shp):
    with fiona.open(path_coutwildrnp_shp, ignore_geometry=True) as collection:
        features = read_vectorized(collection)
        assert features["geometry"] is None

@requires_gpkg
def test_binary_field(tmpdir):
    filename = str(tmpdir.join("test.gpkg"))
    write_binary_gpkg(filename)

    with fiona.open(filename, "r") as collection:
        print(collection.schema)
        features = read_vectorized(collection)

        assert(features["properties"]["name"][0] == "test")
        data = features["properties"]["data"][0]
        assert(binascii.b2a_hex(data) == b"deadbeef")

@requires_gpkg  # ESRI Shapefile doesn't support datetime fields
def test_datetime_fields(tmpdir):
    filename = str(tmpdir.join("test.gpkg"))
    schema = {
        "geometry": "Point",
        "properties": [
            ("date", "date"),
            ("datetime", "datetime"),
            ("nulldt", "datetime"),
        ]
    }
    with fiona.open(filename, "w", driver="GPKG", schema=schema) as dst:
        feature = {
            "geometry": None,
            "properties": {
                "date": "2018-03-24",
                "datetime": "2018-03-24T15:06:01",
                "nulldt": None,
            }
        }
        dst.write(feature)

    with fiona.open(filename, "r") as src:
        features = read_vectorized(src)

        assert features["properties"]["date"].dtype.name == "datetime64[D]"
        assert features["properties"]["datetime"].dtype.name == "datetime64[s]"
        assert features["properties"]["nulldt"].dtype.name == "datetime64[s]"

        assert features["properties"]["date"][0] == np.datetime64("2018-03-24")
        assert features["properties"]["datetime"][0] == np.datetime64("2018-03-24T15:06:01")
        assert str(features["properties"]["nulldt"][0]) == "NaT"

def test_wkb(path_coutwildrnp_shp):
    with fiona.open(path_coutwildrnp_shp, "r") as collection:
        features = read_vectorized(collection, use_wkb=True)

    geometry = features["geometry"][0]
    assert geometry[0:1] == b"\x01"  # little endian
    assert geometry[1:5] == b"\x03\x00\x00\x00"  # polygon
    assert geometry[5:9] == b"\x01\x00\x00\x00"  # 1 ring
    assert len(geometry) == 1325
