import os
import pytest
import fiona

has_gpkg = "GPKG" in fiona.supported_drivers.keys()

@pytest.mark.skipif(not has_gpkg, reason="Requires geopackage driver")
def test_read_gpkg(path_coutwildrnp_gpkg):
    """
    Implicitly tests writing gpkg as the fixture will create the data source on
    first request
    """
    with fiona.open(path_coutwildrnp_gpkg, "r") as src:
        assert len(src) == 67
        feature = next(iter(src))
        assert feature["geometry"]["type"] == "Polygon"
        assert feature["properties"]["NAME"] == "Mount Naomi Wilderness"

@pytest.mark.skipif(not has_gpkg, reason="Requires geopackage driver")
def test_write_gpkg(tmpdir):
    schema = {
        'geometry': 'Point',
        'properties': [('title', 'str')],
    }
    crs = {
        'a': 6370997,
        'lon_0': -100,
        'y_0': 0,
        'no_defs': True,
        'proj': 'laea',
        'x_0': 0,
        'units': 'm',
        'b': 6370997,
        'lat_0': 45,
    }

    path = str(tmpdir.join('foo.gpkg'))

    with fiona.open(path, 'w',
                    driver='GPKG',
                    schema=schema,
                    crs=crs) as dst:
        dst.writerecords([{
            'geometry': {'type': 'Point', 'coordinates': [0.0, 0.0]},
            'properties': {'title': 'One'}}])
        dst.writerecords([{
            'geometry': {'type': 'Point', 'coordinates': [2.0, 3.0]},
            'properties': {'title': 'Two'}}])
        dst.write({
            'geometry': {'type': 'Point', 'coordinates': [20.0, 30.0]},
            'properties': {'title': 'Three'}})
    with fiona.open(path) as src:
        assert src.schema['geometry'] == 'Point'
        assert src.crs == crs
        assert len(src) == 3
