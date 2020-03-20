"""Tests of driver support"""

import pytest

from .conftest import requires_gdal24, get_temp_filename
from fiona.drvsupport import supported_drivers, driver_mode_mingdal
import fiona.drvsupport
from fiona.env import getenv, GDALVersion


@requires_gdal24
@pytest.mark.parametrize('format', ['GeoJSON', 'ESRIJSON', 'TopoJSON', 'GeoJSONSeq'])
def test_geojsonseq(format):
    """Format is available"""
    assert format in fiona.drvsupport.supported_drivers.keys()

blacklist_append_drivers = set(['CSV', 'GPX', 'GPSTrackMaker', 'DXF', 'DGN'])
append_drivers = [driver for driver, raw in supported_drivers.items() if 'a' in raw and driver not in blacklist_append_drivers]

@pytest.mark.parametrize('driver', append_drivers)
def test_append_works(tmpdir, driver):
    """ Test if driver supports append mode.
    
    Some driver only allow a specific schema. These drivers can be excluded by adding them to blacklist_append_drivers.
    
    """

    path = str(tmpdir.join(get_temp_filename(driver)))

    # If driver is not able to write, we cannot test append
    if driver in driver_mode_mingdal['w'] and GDALVersion.runtime() < GDALVersion(*driver_mode_mingdal['w'][driver][:2]):
        return

    with fiona.open(path, 'w',
                    driver=driver,
                    schema={'geometry': 'LineString',
                            'properties': [('title', 'str')]}) as c:

        c.writerecords([{'geometry': {'type': 'LineString', 'coordinates': [
                       (1.0, 0.0), (0.0, 0.0)]}, 'properties': {'title': 'One'}}])

    if driver in driver_mode_mingdal['a'] and GDALVersion.runtime() < GDALVersion(*driver_mode_mingdal['a'][driver][:2]):
        with pytest.raises(DriverError):
            with fiona.open(path, 'a',
                        driver=driver) as c:
                c.writerecords([{'geometry': {'type': 'LineString', 'coordinates': [
                            (2.0, 0.0), (0.0, 0.0)]}, 'properties': {'title': 'Two'}}])

    else:
        with fiona.open(path, 'a',
                        driver=driver) as c:
            c.writerecords([{'geometry': {'type': 'LineString', 'coordinates': [
                        (2.0, 0.0), (0.0, 0.0)]}, 'properties': {'title': 'Two'}}])

        with fiona.open(path) as c:
            assert c.driver == driver
            assert len([f for f in c]) == 2


write_not_append_drivers = [driver for driver, raw in supported_drivers.items() if 'w' in raw and not 'a' in raw]
@pytest.mark.parametrize('driver', write_not_append_drivers)
def test_append_does_not_work(tmpdir, driver):
    """Test if driver supports append but it is not enabled
    
    If this test fails, it should be considered to enable append for the respective driver in drvsupport.py. 
    
    """
    
    if driver == 'BNA' and GDALVersion.runtime() < GDALVersion(2, 0):
        # BNA driver segfaults with gdal 1.11
        return

    backup_mode = supported_drivers[driver]
    supported_drivers[driver] = 'raw'

    path = str(tmpdir.join(get_temp_filename(driver)))

    with fiona.open(path, 'w',
                    driver=driver,
                    schema={'geometry': 'LineString',
                            'properties': [('title', 'str')]}) as c:

        c.writerecords([{'geometry': {'type': 'LineString', 'coordinates': [
                       (1.0, 0.0), (0.0, 0.0)]}, 'properties': {'title': 'One'}}])

    with pytest.raises(Exception):
        with fiona.open(path, 'a',
                    driver=driver) as c:
            c.writerecords([{'geometry': {'type': 'LineString', 'coordinates': [
                        (2.0, 0.0), (0.0, 0.0)]}, 'properties': {'title': 'Two'}}])

    supported_drivers[driver] = backup_mode


only_read_drivers = [driver for driver, raw in supported_drivers.items() if raw == 'r']
@pytest.mark.parametrize('driver', only_read_drivers)
def test_readonly_driver_cannot_write(tmpdir, driver):
    """Test if read only driver cannot write
    
    If this test fails, it should be considered to enable write support for the respective driver in drvsupport.py. 
    
    """
    
    if driver == 'BNA' and GDALVersion.runtime() < GDALVersion(2, 0):
        # BNA driver segfaults with gdal 1.11
        return

    backup_mode = supported_drivers[driver]
    supported_drivers[driver] = 'rw'

    path = str(tmpdir.join(get_temp_filename(driver)))

    with pytest.raises(Exception):
        with fiona.open(path, 'w',
                        driver=driver,
                        schema={'geometry': 'LineString',
                                'properties': [('title', 'str')]}) as c:

            c.writerecords([{'geometry': {'type': 'LineString', 'coordinates': [
                        (1.0, 0.0), (0.0, 0.0)]}, 'properties': {'title': 'One'}}])
    
    supported_drivers[driver] = backup_mode


@pytest.mark.parametrize('driver', driver_mode_mingdal['w'].keys())
def test_write_mode_not_supported(tmpdir, driver):
    """ Test if DriverError is raised when write mode is not supported for old versions of GDAL
    """

    if GDALVersion.runtime() >= GDALVersion(*driver_mode_mingdal['w'][driver][:2]):
        return

    path = str(tmpdir.join(get_temp_filename(driver)))

    with pytest.raises(DriverError):
        with fiona.open(path, 'w',
                driver=driver,
                schema={'geometry': 'LineString',
                        'properties': [('title', 'str')]}) as c:

            c.writerecords([{'geometry': {'type': 'LineString', 'coordinates': [
                    (1.0, 0.0), (0.0, 0.0)]}, 'properties': {'title': 'One'}}])


def test_driver_mode_mingdal():
    """
        Test if mode and driver is enabled in supported_drivers
    """
    
    for mode in driver_mode_mingdal:
        for driver in driver_mode_mingdal[mode]:
            if driver in supported_drivers:
                assert mode in supported_drivers[driver]
