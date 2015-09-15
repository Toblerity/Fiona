import os
import tempfile

import fiona


def test_profile():
    with fiona.open('tests/data/coutwildrnp.shp') as src:
        assert src.meta['crs_wkt'] == 'GEOGCS["GCS_WGS_1984",DATUM["WGS_1984",SPHEROID["WGS_84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295],AUTHORITY["EPSG","4326"]]'


def test_profile_creation_wkt():
    tmpdir = tempfile.mkdtemp()
    outfilename = os.path.join(tmpdir, 'test.shp')
    with fiona.open('tests/data/coutwildrnp.shp') as src:
        profile = src.meta
        profile['crs'] = 'bogus'
        with fiona.open(outfilename, 'w', **profile) as dst:
            assert dst.crs == {'init': 'epsg:4326'}
            assert dst.crs_wkt == 'GEOGCS["GCS_WGS_1984",DATUM["WGS_1984",SPHEROID["WGS_84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295],AUTHORITY["EPSG","4326"]]'
