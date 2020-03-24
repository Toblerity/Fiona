"""Tests of driver support"""

import pytest

from .conftest import requires_gdal24, get_temp_filename
from fiona.drvsupport import supported_drivers, driver_mode_mingdal
import fiona.drvsupport
from fiona.env import GDALVersion
from fiona.errors import DriverError

blacklist_append_drivers = {'CSV', 'GPX', 'GPSTrackMaker', 'DXF', 'DGN'}
blacklist_write_drivers = {'CSV', 'GPX', 'GPSTrackMaker', 'DXF', 'DGN'}


@requires_gdal24
@pytest.mark.parametrize('format', ['GeoJSON', 'ESRIJSON', 'TopoJSON', 'GeoJSONSeq'])
def test_geojsonseq(format):
    """Format is available"""
    assert format in fiona.drvsupport.supported_drivers.keys()


@pytest.mark.parametrize('driver', [driver for driver, raw in supported_drivers.items() if 'w' in raw
                                    and driver not in blacklist_write_drivers])
def test_write(tmpdir, driver):
    """
        Test if write mode works.

    """

    if driver == "BNA" and GDALVersion.runtime() < GDALVersion(2, 0):
        # BNA driver segfaults with gdal 1.11
        return

    path = str(tmpdir.join(get_temp_filename(driver)))

    if driver in driver_mode_mingdal['w'] and GDALVersion.runtime() < GDALVersion(
            *driver_mode_mingdal['w'][driver][:2]):

        # Test if DriverError is raised for gdal < driver_mode_mingdal
        with pytest.raises(DriverError):
            with fiona.open(path, 'w',
                            driver=driver,
                            schema={'geometry': 'LineString',
                                    'properties': [('title', 'str')]}) as c:
                c.writerecords([{'geometry': {'type': 'LineString', 'coordinates': [
                    (1.0, 0.0), (0.0, 0.0)]}, 'properties': {'title': 'One'}}])

    else:

        # Test if we can write
        with fiona.open(path, 'w',
                        driver=driver,
                        schema={'geometry': 'LineString',
                                'properties': [('title', 'str')]}) as c:

            c.writerecords([{'geometry': {'type': 'LineString', 'coordinates': [
                (1.0, 0.0), (0.0, 0.0)]}, 'properties': {'title': 'One'}}])

        with fiona.open(path) as c:
            assert c.driver == driver
            assert len([f for f in c]) == 1


@pytest.mark.parametrize('driver', [driver for driver in driver_mode_mingdal['w'].keys()
                                    if driver not in blacklist_append_drivers
                                    and driver in supported_drivers])
def test_write_mingdal(tmpdir, driver):
    """
        Test if driver really can't write for gdal < driver_mode_mingdal

        If this test fails, it should be considered to update driver_mode_mingdal in drvsupport.py.

    """

    if driver == "BNA" and GDALVersion.runtime() < GDALVersion(2, 0):
        # BNA driver segfaults with gdal 1.11
        return

    path = str(tmpdir.join(get_temp_filename(driver)))

    if driver in driver_mode_mingdal['w'] and GDALVersion.runtime() < GDALVersion(
            *driver_mode_mingdal['w'][driver][:2]):
        min_version_backup = driver_mode_mingdal['w'][driver]
        driver_mode_mingdal['w'].pop(driver)

        with pytest.raises(Exception):
            with fiona.open(path, 'w',
                            driver=driver,
                            schema={'geometry': 'LineString',
                                    'properties': [('title', 'str')]}) as c:
                c.writerecords([{'geometry': {'type': 'LineString', 'coordinates': [
                    (1.0, 0.0), (0.0, 0.0)]}, 'properties': {'title': 'One'}}])

        driver_mode_mingdal['w'][driver] = min_version_backup


@pytest.mark.parametrize('driver', [driver for driver, raw in supported_drivers.items() if 'a' in raw
                                    and driver not in blacklist_append_drivers])
def test_append(tmpdir, driver):
    """ Test if driver supports append mode.
    
    Some driver only allow a specific schema. These drivers can be excluded by adding them to blacklist_append_drivers.
    
    """

    if driver == "BNA" and GDALVersion.runtime() < GDALVersion(2, 0):
        # BNA driver segfaults with gdal 1.11
        return

    path = str(tmpdir.join(get_temp_filename(driver)))

    # If driver is not able to write, we cannot test append
    if driver in driver_mode_mingdal['w'] and GDALVersion.runtime() < GDALVersion(
            *driver_mode_mingdal['w'][driver][:2]):
        return

    # Create test file to append to
    with fiona.open(path, 'w',
                    driver=driver,
                    schema={'geometry': 'LineString',
                            'properties': [('title', 'str')]}) as c:

        c.writerecords([{'geometry': {'type': 'LineString', 'coordinates': [
            (1.0, 0.0), (0.0, 0.0)]}, 'properties': {'title': 'One'}}])

    if driver in driver_mode_mingdal['a'] and GDALVersion.runtime() < GDALVersion(
            *driver_mode_mingdal['a'][driver][:2]):

        # Test if DriverError is raised for gdal < driver_mode_mingdal
        with pytest.raises(DriverError):
            with fiona.open(path, 'a',
                            driver=driver) as c:
                c.writerecords([{'geometry': {'type': 'LineString', 'coordinates': [
                    (2.0, 0.0), (0.0, 0.0)]}, 'properties': {'title': 'Two'}}])

    else:
        # Test if we can append
        with fiona.open(path, 'a',
                        driver=driver) as c:
            c.writerecords([{'geometry': {'type': 'LineString', 'coordinates': [
                (2.0, 0.0), (0.0, 0.0)]}, 'properties': {'title': 'Two'}}])

        with fiona.open(path) as c:
            assert c.driver == driver
            assert len([f for f in c]) == 2


@pytest.mark.parametrize('driver', [driver for driver in driver_mode_mingdal['a'].keys()
                                    if driver not in blacklist_append_drivers
                                    and driver in supported_drivers])
def test_append_mingdal(tmpdir, driver):
    """ Test if driver supports append mode.

    Some driver only allow a specific schema. These drivers can be excluded by adding them to blacklist_append_drivers.

    If this test fails, it should be considered to update driver_mode_mingdal in drvsupport.py.

    """

    if driver == "BNA" and GDALVersion.runtime() < GDALVersion(2, 0):
        # BNA driver segfaults with gdal 1.11
        return

    path = str(tmpdir.join(get_temp_filename(driver)))

    # If driver is not able to write, we cannot test append
    if driver in driver_mode_mingdal['w'] and GDALVersion.runtime() < GDALVersion(
            *driver_mode_mingdal['w'][driver][:2]):
        return

    # Create test file to append to
    with fiona.open(path, 'w',
                    driver=driver,
                    schema={'geometry': 'LineString',
                            'properties': [('title', 'str')]}) as c:

        c.writerecords([{'geometry': {'type': 'LineString', 'coordinates': [
            (1.0, 0.0), (0.0, 0.0)]}, 'properties': {'title': 'One'}}])

    if driver in driver_mode_mingdal['a'] and GDALVersion.runtime() < GDALVersion(
            *driver_mode_mingdal['a'][driver][:2]):
        # Test if driver really can't append for gdal < driver_mode_mingdal
        min_version_backup = driver_mode_mingdal['a'][driver]
        driver_mode_mingdal['a'].pop(driver)

        with pytest.raises(Exception):
            with fiona.open(path, 'a',
                            driver=driver) as c:
                c.writerecords([{'geometry': {'type': 'LineString', 'coordinates': [
                    (2.0, 0.0), (0.0, 0.0)]}, 'properties': {'title': 'Two'}}])

            with fiona.open(path) as c:
                assert c.driver == driver
                assert len([f for f in c]) == 2

        driver_mode_mingdal['a'] = min_version_backup


@pytest.mark.parametrize('driver', [driver for driver, raw in supported_drivers.items() if
                                    raw == 'r' and driver not in blacklist_write_drivers])
def test_readonly_driver_cannot_write(tmpdir, driver):
    """Test if read only driver cannot write
    
    If this test fails, it should be considered to enable write support for the respective driver in drvsupport.py. 
    
    """

    if driver == "BNA" and GDALVersion.runtime() < GDALVersion(2, 0):
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


@pytest.mark.parametrize('driver', [driver for driver, raw in supported_drivers.items() if
                                    'w' in raw and driver not in blacklist_append_drivers])
def test_write_driver_cannot_append(tmpdir, driver):
    """
    Test if a driver that supports write cannot also append

    If this test fails, it should be considered to enable append support for the respective driver in drvsupport.py.

    """

    if driver == "BNA" and GDALVersion.runtime() < GDALVersion(2, 0):
        # BNA driver segfaults with gdal 1.11
        return

    path = str(tmpdir.join(get_temp_filename(driver)))

    # If driver is not able to write, we cannot test append
    if driver in driver_mode_mingdal['w'] and GDALVersion.runtime() < GDALVersion(
            *driver_mode_mingdal['w'][driver][:2]):
        return

    backup_mode = supported_drivers[driver]
    supported_drivers[driver] = 'rw'

    # Create test file to append to
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

        with fiona.open(path) as c:
            assert c.driver == driver
            assert len([f for f in c]) == 2

    supported_drivers[driver] = backup_mode


def test_driver_mode_mingdal():
    """
        Test if mode and driver is enabled in supported_drivers
    """

    for mode in driver_mode_mingdal:
        for driver in driver_mode_mingdal[mode]:
            # we cannot test drivers that are not present in the gdal installation
            if driver in supported_drivers:
                assert mode in supported_drivers[driver]
