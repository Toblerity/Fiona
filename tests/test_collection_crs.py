import os
import tempfile

import fiona
import fiona.crs


def test_collection_crs_wkt():
    with fiona.open('tests/data/coutwildrnp.shp') as src:
        assert src.crs_wkt.startswith(
            'GEOGCS["GCS_WGS_1984",DATUM["WGS_1984",SPHEROID["WGS_84"')


def test_collection_no_crs_wkt():
    """crs members of a dataset with no crs can be accessed safely."""
    tmpdir = tempfile.gettempdir()
    filename = os.path.join(tmpdir, 'test.shp')
    with fiona.open('tests/data/coutwildrnp.shp') as src:
        profile = src.meta
    del profile['crs']
    del profile['crs_wkt']
    with fiona.open(filename, 'w', **profile) as dst:
        assert dst.crs_wkt == ""
        assert dst.crs == {}
