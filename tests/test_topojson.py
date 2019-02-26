"""
Support for TopoJSON was added in OGR 1.11 to the `GeoJSON` driver.
Starting at GDAL 2.3 support was moved to the `TopoJSON` driver.
"""

import fiona
from fiona.env import GDALVersion
import os
import pytest
from collections import OrderedDict

gdal_version = GDALVersion.runtime()

driver = "TopoJSON" if gdal_version.at_least((2, 3)) else "GeoJSON"
has_driver = driver in fiona.drvsupport.supported_drivers.keys()


@pytest.mark.skipif(not gdal_version.at_least((1, 11)), reason="Requires GDAL >= 1.11")
@pytest.mark.skipif(not has_driver, reason="Requires {} driver".format(driver))
def test_read_topojson(data_dir):
    with fiona.open(os.path.join(data_dir, "example.topojson"), "r") as collection:
        assert len(collection) == 3
        features = list(collection)

    expected_features = [
        {
            "type": "Feature",
            "id": "0",
            "properties": OrderedDict([("id", None), ("prop0", "value0"), ("prop1", None)]),
            "geometry": {"type": "Point", "coordinates": (102.0, 0.5)}
        },
        {
            "type": "Feature",
            "id": "1",
            "properties": OrderedDict([("id", None), ("prop0", "value0"), ("prop1", "0")]),
            "geometry": {"type": "LineString", "coordinates": [(102.0, 0.0), (103.0, 1.0), (104.0, 0.0), (105.0, 1.0)]}
        },
        {
            "type": "Feature",
            "id": "2",
            "properties": OrderedDict([("id", None), ("prop0", "value0"), ("prop1", {"this": "that"})]),
            "geometry": {"type": "Polygon", "coordinates": [[(100.0, 0.0), (100.0, 1.0), (101.0, 1.0), (101.0, 0.0), (100.0, 0.0)]]}
        }
    ]

    assert features == expected_features
