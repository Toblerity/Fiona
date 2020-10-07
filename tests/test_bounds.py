import pytest
from fiona._env import get_gdal_version_tuple

import fiona
from fiona.drvsupport import supported_drivers, _driver_supports_mode
from fiona.errors import DriverError
from fiona.env import GDALVersion
from tests.conftest import get_temp_filename


def test_bounds_point():
    g = {'type': 'Point', 'coordinates': [10, 10]}
    assert fiona.bounds(g) == (10, 10, 10, 10)


def test_bounds_line():
    g = {'type': 'LineString', 'coordinates': [[0, 0], [10, 10]]}
    assert fiona.bounds(g) == (0, 0, 10, 10)


def test_bounds_polygon():
    g = {'type': 'Polygon', 'coordinates': [[[0, 0], [10, 10], [10, 0]]]}
    assert fiona.bounds(g) == (0, 0, 10, 10)


def test_bounds_z():
    g = {'type': 'Point', 'coordinates': [10, 10, 10]}
    assert fiona.bounds(g) == (10, 10, 10, 10)


@pytest.mark.parametrize('driver', [driver for driver in supported_drivers if _driver_supports_mode(driver, 'w')])
def test_bounds(tmpdir, driver, testdata_generator):
    """Test if bounds are correctly calculated after writing
    """
    if driver == 'BNA' and GDALVersion.runtime() < GDALVersion(2, 0):
        pytest.skip("BNA driver segfaults with gdal 1.11")
    if driver == 'MapInfo File':
        pytest.skip(
            "MapInfo File driver is not able to calcualte bounds: (-30000000.0, -15000000.0, 30000000.0, 15000000.0) ")
    if driver == 'ESRI Shapefile' and get_gdal_version_tuple() < (3, 1):
        pytest.skip("Bug in GDALs Shapefile driver: https://github.com/OSGeo/gdal/issues/2269")

    range1 = list(range(0, 5))
    range2 = list(range(5, 10))
    schema, crs, records1, records2, test_equal = testdata_generator(driver, range1, range2)

    if not schema['geometry'] == 'Point':
        pytest.skip("Driver does not support point geometries")

    filename = get_temp_filename(driver)
    path = str(tmpdir.join(filename))

    def calc_bounds(records):
        xs = []
        ys = []
        for r in records:
            xs.append(r['geometry']['coordinates'][0])
            ys.append(r['geometry']['coordinates'][1])
        return min(xs), max(xs), min(ys), max(ys)

    with fiona.open(path, 'w',
                    driver=driver,
                    schema=schema) as c:
        c.writerecords(records1)
        try:
            bounds = c.bounds
            assert bounds == calc_bounds(records1)
        except Exception as e:
            assert isinstance(e, DriverError)

        c.writerecords(records2)
        try:
            bounds = c.bounds
            assert bounds == calc_bounds(records1 + records2)
        except Exception as e:
            assert isinstance(e, DriverError)
