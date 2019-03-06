"""Tests of the ogrext.Session class"""

import fiona


def test_get(path_coutwildrnp_shp):
    with fiona.open(path_coutwildrnp_shp) as col:
        feat3 = col.get(2)
        assert feat3['properties']['NAME'] == 'Mount Zirkel Wilderness'
