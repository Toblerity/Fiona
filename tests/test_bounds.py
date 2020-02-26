import fiona
import pytest
from fiona.drvsupport import supported_drivers
from .conftest import driver_extensions

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
    g = {'type': 'Point', 'coordinates': [10,10,10]}
    assert fiona.bounds(g) == (10, 10, 10, 10)


blacklist_write_drivers = set(['CSV', 'GPX', 'GPSTrackMaker', 'DXF', 'DGN'])
write_drivers = [driver for driver, raw in supported_drivers.items() if 'w' in raw and driver not in blacklist_write_drivers]
@pytest.mark.parametrize('driver', write_drivers)
def test_bounds(tmpdir, driver):
    """Test if bounds are correctly calculated after writing
    
    """
    extension = driver_extensions.get(driver, "bar")
    path = str(tmpdir.join('foo.{}'.format(extension)))

    with fiona.open(path, 'w',
                    driver=driver,
                    schema={'geometry': 'Point',
                            'properties': [('title', 'str')]},
                    fiona_force_driver=True) as c:

        c.writerecords([{'geometry': {'type': 'Point', 'coordinates': (1.0, 10.0)},
                            'properties': {'title': 'One'}}])

        assert c.bounds == (1.0, 10.0, 1.0, 10.0)

        c.writerecords([{'geometry': {'type': 'Point', 'coordinates': (2.0, 20.0)},
                            'properties': {'title': 'One'}}])
        
        assert c.bounds == (1.0, 10.0, 2.0, 20.0)
