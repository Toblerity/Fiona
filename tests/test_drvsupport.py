"""Tests of driver support"""

import pytest

from .conftest import requires_gdal24, get_temp_filename
from fiona.drvsupport import supported_drivers, driver_mode_mingdal
import fiona.drvsupport
from fiona.env import GDALVersion
from fiona.errors import DriverError
from collections import OrderedDict

blacklist_append_drivers = {'CSV', 'DXF', 'DGN'}
blacklist_write_drivers = {'CSV', 'DXF', 'DGN'}


def get_schema(driver):
    schemas = {
        'GPX': {'properties': OrderedDict([('ele', 'float'), ('time', 'datetime')]),
                'geometry': 'Point'},
        'GPSTrackMaker': {'properties': OrderedDict([('ele', 'float'), ('time', 'datetime')]),
                          'geometry': 'Point'}
    }
    default_schema = {'geometry': 'LineString',
                      'properties': [('title', 'str')]}
    return schemas.get(driver, default_schema)


def get_records_1(driver):
    records = {
        'GPX': {'type': 'Feature', 'properties': OrderedDict([('ele', 386.3), ('time', '2020-03-24T16:08:40')]),
                'geometry': {'type': 'Point', 'coordinates': (8.306711, 47.475623)}},
        'GPSTrackMaker': {'type': 'Feature',
                          'properties': OrderedDict([('ele', 386.3), ('time', '2020-03-24T16:08:40')]),
                          'geometry': {'type': 'Point', 'coordinates': (8.306711, 47.475623)}}
    }

    default_record = {'geometry': {'type': 'LineString', 'coordinates': [
        (1.0, 0.0), (0.0, 0.0)]}, 'properties': {'title': 'One'}}

    return records.get(driver, default_record)


def get_records_2(driver):
    records = {
        'GPX': {'properties': OrderedDict([('ele', 386.3), ('time', '2020-03-24T16:19:14')]),
                'geometry': {'type': 'Point', 'coordinates': (8.307451, 47.474996)}}
        'GPSTrackMaker': {'properties': OrderedDict([('ele', 386.3), ('time', '2020-03-24T16:19:14')]),
                          'geometry': {'type': 'Point', 'coordinates': (8.307451, 47.474996)}}
    }

    default_record = {'geometry': {'type': 'LineString', 'coordinates': [
        (2.0, 0.0), (0.0, 0.0)]}, 'properties': {'title': 'Two'}}

    return records.get(driver, default_record)


@requires_gdal24
@pytest.mark.parametrize('format', ['GeoJSON', 'ESRIJSON', 'TopoJSON', 'GeoJSONSeq'])
def test_geojsonseq(format):
    """Format is available"""
    assert format in fiona.drvsupport.supported_drivers.keys()


@pytest.mark.parametrize('driver', [driver for driver, raw in supported_drivers.items() if 'w' in raw
                                    and driver not in blacklist_write_drivers])
def test_write_or_driver_error(tmpdir, driver):
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
                            schema=get_schema(driver)) as c:
                c.write(get_records_1(driver))

    else:

        # Test if we can write
        with fiona.open(path, 'w',
                        driver=driver,
                        schema=get_schema(driver)) as c:

            c.write(get_records_1(driver))

        with fiona.open(path) as c:
            assert c.driver == driver
            assert len([f for f in c]) == 1


@pytest.mark.parametrize('driver', [driver for driver in driver_mode_mingdal['w'].keys()
                                    if driver not in blacklist_append_drivers
                                    and driver in supported_drivers])
def test_write_does_not_work_when_gdal_smaller_mingdal(tmpdir, driver):
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
                            schema=get_schema(driver)) as c:
                c.write(get_records_1(driver))

        driver_mode_mingdal['w'][driver] = min_version_backup


@pytest.mark.parametrize('driver', [driver for driver, raw in supported_drivers.items() if 'a' in raw
                                    and driver not in blacklist_append_drivers])
def test_append_or_driver_error(tmpdir, driver):
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
                    schema=get_schema(driver)) as c:

        c.write(get_records_1(driver))

    if driver in driver_mode_mingdal['a'] and GDALVersion.runtime() < GDALVersion(
            *driver_mode_mingdal['a'][driver][:2]):

        # Test if DriverError is raised for gdal < driver_mode_mingdal
        with pytest.raises(DriverError):
            with fiona.open(path, 'a',
                            driver=driver) as c:
                c.write(get_records_2(driver))

    else:
        # Test if we can append
        with fiona.open(path, 'a',
                        driver=driver) as c:
            c.write(get_records_2(driver))

        with fiona.open(path) as c:
            assert c.driver == driver
            assert len([f for f in c]) == 2


@pytest.mark.parametrize('driver', [driver for driver in driver_mode_mingdal['a'].keys()
                                    if driver not in blacklist_append_drivers
                                    and driver in supported_drivers])
def test_append_does_not_work_when_gdal_smaller_mingdal(tmpdir, driver):
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
                    schema=get_schema(driver)) as c:

        c.write(get_records_1(driver))

    if driver in driver_mode_mingdal['a'] and GDALVersion.runtime() < GDALVersion(
            *driver_mode_mingdal['a'][driver][:2]):
        # Test if driver really can't append for gdal < driver_mode_mingdal
        min_version_backup = driver_mode_mingdal['a'][driver]
        driver_mode_mingdal['a'].pop(driver)

        with pytest.raises(Exception):
            with fiona.open(path, 'a',
                            driver=driver) as c:
                c.write(get_records_2(driver))

            with fiona.open(path) as c:
                assert c.driver == driver
                assert len([f for f in c]) == 2

        driver_mode_mingdal['a'] = min_version_backup


@pytest.mark.parametrize('driver', [driver for driver, raw in supported_drivers.items() if
                                    raw == 'r' and driver not in blacklist_write_drivers])
def test_no_write_driver_cannot_write(tmpdir, driver):
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
                        schema=get_schema(driver)) as c:
            c.write(get_records_1(driver))

    supported_drivers[driver] = backup_mode


@pytest.mark.parametrize('driver', [driver for driver, raw in supported_drivers.items() if
                                    'w' in raw and 'a' not in raw and driver not in blacklist_append_drivers])
def test_no_append_driver_cannot_append(tmpdir, driver):
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
    supported_drivers[driver] = 'raw'

    # Create test file to append to
    with fiona.open(path, 'w',
                    driver=driver,
                    schema=get_schema(driver)) as c:

        c.write(get_records_1(driver))

    with pytest.raises(Exception):
        with fiona.open(path, 'a',
                        driver=driver) as c:
            c.write(get_records_2(driver))

        with fiona.open(path) as c:
            assert c.driver == driver
            assert len([f for f in c]) == 2

    supported_drivers[driver] = backup_mode


def test_mingdal_drivers_are_supported():
    """
        Test if mode and driver is enabled in supported_drivers
    """

    for mode in driver_mode_mingdal:
        for driver in driver_mode_mingdal[mode]:
            # we cannot test drivers that are not present in the gdal installation
            if driver in supported_drivers:
                assert mode in supported_drivers[driver]
