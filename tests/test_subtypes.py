import fiona
import six

def test_read_bool_subtype(tmpdir):
    test_data = """{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"bool": true, "not_bool": 1, "float": 42.5}, "geometry": null}]}"""
    path = tmpdir.join("test_read_bool_subtype.geojson")
    with open(str(path), "w") as f:
        f.write(test_data)
    
    with fiona.open(str(path), "r") as src:
        feature = next(iter(src))
    
    if fiona.gdal_version.major >= 2:
        assert type(feature["properties"]["bool"]) is bool
    else:
        assert type(feature["properties"]["bool"]) is int
    assert isinstance(feature["properties"]["not_bool"], six.integer_types)
    assert type(feature["properties"]["float"]) is float

def test_write_bool_subtype(tmpdir):
    path = tmpdir.join("test_write_bool_subtype.geojson")
    
    schema = {
        "geometry": "Point",
        "properties": {
            "bool": "bool",
            "not_bool": "int",
            "float": "float",
        }
    }
    
    feature = {
        "geometry": None,
        "properties": {
            "bool": True,
            "not_bool": 1,
            "float": 42.5,
        }
    }

    with fiona.open(str(path), "w", driver="GeoJSON", schema=schema) as dst:
        dst.write(feature)
    
    with open(str(path), "r") as f:
        data = f.read()
    
    if fiona.gdal_version.major >= 2:
        assert """"bool": true""" in data
    else:
        assert """"bool": 1""" in data
    assert """"not_bool": 1""" in data
