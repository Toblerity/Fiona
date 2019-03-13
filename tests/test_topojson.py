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
    """Test reading a TopoJSON file

    The TopoJSON support in GDAL is a little unpredictable. In some versions
    the geometries or properties aren't parsed correctly. Here we just check
    that we can open the file, get the right number of features out, and
    that they have a geometry and some properties. See GH#722.
    """
    with fiona.open(os.path.join(data_dir, "example.topojson"), "r") as collection:
        features = list(collection)

    assert len(features) == 3, "unexpected number of features"
    for feature in features:
        assert isinstance(feature["properties"], OrderedDict)
        assert len(feature["properties"]) > 0
        assert feature["geometry"]["type"] in {"Point", "LineString", "Polygon"}
