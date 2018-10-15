import os
import re

import fiona
import fiona.crs

from .conftest import WGS84PATTERN, requires_gdal2


def test_collection_crs_wkt(path_coutwildrnp_shp):
    with fiona.open(path_coutwildrnp_shp) as src:
        assert re.match(WGS84PATTERN, src.crs_wkt)


def test_collection_no_crs_wkt(tmpdir, path_coutwildrnp_shp):
    """crs members of a dataset with no crs can be accessed safely."""
    filename = str(tmpdir.join("test.shp"))
    with fiona.open(path_coutwildrnp_shp) as src:
        profile = src.meta
    del profile['crs']
    del profile['crs_wkt']
    with fiona.open(filename, 'w', **profile) as dst:
        assert dst.crs_wkt == ""
        assert dst.crs == {}


@requires_gdal2
def test_collection_create_crs_wkt(tmpdir):
    """A collection can be created using crs_wkt"""
    filename = str(tmpdir.join("test.shp"))
    wkt = 'GEOGCS["GCS_WGS_1984",DATUM["WGS_1984",SPHEROID["WGS_84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295],AUTHORITY["EPSG","4326"]]'
    with fiona.open(filename, 'w', schema={'geometry': 'Point', 'properties': {'foo': 'int'}}, crs_wkt=wkt, driver='GeoJSON') as dst:
        assert dst.crs_wkt == wkt

    with fiona.open(filename) as col:
        assert col.crs_wkt.startswith('GEOGCS["WGS 84')
