import os
import re

import fiona
import fiona.crs

from .conftest import WGS84PATTERN

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
