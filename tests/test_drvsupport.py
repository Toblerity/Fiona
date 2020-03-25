"""Tests of driver support"""

import pytest

from .conftest import requires_gdal24, get_temp_filename
from fiona.drvsupport import supported_drivers, driver_mode_mingdal
import fiona.drvsupport
from fiona.env import GDALVersion
from fiona.errors import DriverError
from collections import OrderedDict

# Add drivers to blacklist while testing write or append
blacklist_write_drivers = {}
blacklist_append_drivers = {}


def get_schema(driver):
    """
    Generate schema for each driver
    """
    schemas = {
        'GPX': {'properties': OrderedDict([('ele', 'float'),
                                           ('time', 'datetime')]),
                'geometry': 'Point'},
        'GPSTrackMaker': {'properties': OrderedDict([]),
                          'geometry': 'Point'},
        'DXF': {'properties': OrderedDict(
            [('Layer', 'str'),
             ('SubClasses', 'str'),
             ('Linetype', 'str'),
             ('EntityHandle', 'str'),
             ('Text', 'str')]),
            'geometry': 'Point'},
        'CSV': {'properties': OrderedDict([('ele', 'float')]),
                'geometry': None},
        'DGN': {'properties': OrderedDict([]),
                'geometry': 'LineString'}
    }
    default_schema = {'geometry': 'LineString',
                      'properties': [('title', 'str')]}
    return schemas.get(driver, default_schema)


def get_record1(driver):
    """
    Generate first record to write depending on driver
    """
    records = {
        'GPX': {'properties': OrderedDict([('ele', 386.3),
                                           ('time', '2020-03-24T16:08:40')]),
                'geometry': {'type': 'Point', 'coordinates': (8.306711, 47.475623)}},
        'GPSTrackMaker': {'properties': OrderedDict([]),
                          'geometry': {'type': 'Point', 'coordinates': (8.306711, 47.475623)}},
        'DXF': {'properties': OrderedDict(
            [('Layer', '0'),
             ('SubClasses', 'AcDbEntity:AcDbPoint'),
             ('Linetype', None),
             ('EntityHandle', '20000'),
             ('Text', None)]),
            'geometry': {'type': 'Point', 'coordinates': (8.306711, 47.475623)}},
        'CSV': {'properties': OrderedDict([('ele', 386.3)]),
                'geometry': None},
        'DGN': {'properties': OrderedDict(
            []),
            'geometry': {'type': 'LineString', 'coordinates': [
                (1.0, 0.0), (0.0, 0.0)]}}
    }

    default_record = {'geometry': {'type': 'LineString', 'coordinates': [
        (1.0, 0.0), (0.0, 0.0)]}, 'properties': {'title': 'One'}}

    return records.get(driver, default_record)


def get_record2(driver):
    """
    Generate second record to write depending on driver
    """
    records = {
        'GPX': {'properties': OrderedDict([('ele', 386.3),
                                           ('time', '2020-03-24T16:19:14')]),
                'geometry': {'type': 'Point', 'coordinates': (8.307451, 47.474996)}},
        'GPSTrackMaker': {'properties': OrderedDict([]),
                          'geometry': {'type': 'Point', 'coordinates': (8.307451, 47.474996)}},
        'DXF': {'properties': OrderedDict(
            [('Layer', '0'),
             ('SubClasses', 'AcDbEntity:AcDbPoint'),
             ('Linetype', None),
             ('EntityHandle', '20000'),
             ('Text', None)]),
            'geometry': {'type': 'Point', 'coordinates': (8.307451, 47.474996)}},
        'CSV': {'properties': OrderedDict([('ele', 386.8)]),
                'geometry': None},
        'DGN': {'properties': OrderedDict(
            [('Type', 3),
             ('Level', 0),
             ('GraphicGroup', 0),
             ('ColorIndex', 0),
             ('Weight', 0),
             ('Style', 0),
             ('EntityNum', None),
             ('MSLink', None),
             ('Text', None)]),
            'geometry': {'type': 'LineString', 'coordinates': [
                (2.0, 0.0), (0.0, 0.0)]}}
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
                c.write(get_record1(driver))

    else:

        # Test if we can write
        with fiona.open(path, 'w',
                        driver=driver,
                        schema=get_schema(driver)) as c:

            c.write(get_record1(driver))

        with fiona.open(path) as c:
            assert c.driver == driver
            assert len([f for f in c]) == 1


@pytest.mark.parametrize('driver', [driver for driver in driver_mode_mingdal['w'].keys()
                                    if driver not in blacklist_append_drivers
                                    and driver in supported_drivers])
def test_write_does_not_work_when_gdal_smaller_mingdal(tmpdir, driver, monkeypatch):
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
        monkeypatch.delitem(fiona.drvsupport.driver_mode_mingdal['w'], driver)

        with pytest.raises(Exception):
            with fiona.open(path, 'w',
                            driver=driver,
                            schema=get_schema(driver)) as c:
                c.write(get_record1(driver))


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

        c.write(get_record1(driver))

    if driver in driver_mode_mingdal['a'] and GDALVersion.runtime() < GDALVersion(
            *driver_mode_mingdal['a'][driver][:2]):

        # Test if DriverError is raised for gdal < driver_mode_mingdal
        with pytest.raises(DriverError):
            with fiona.open(path, 'a',
                            driver=driver) as c:
                c.write(get_record2(driver))

    else:
        # Test if we can append
        with fiona.open(path, 'a',
                        driver=driver) as c:
            c.write(get_record2(driver))

        with fiona.open(path) as c:
            assert c.driver == driver
            assert len([f for f in c]) == 2


@pytest.mark.parametrize('driver', [driver for driver in driver_mode_mingdal['a'].keys()
                                    if driver not in blacklist_append_drivers
                                    and driver in supported_drivers])
def test_append_does_not_work_when_gdal_smaller_mingdal(tmpdir, driver, monkeypatch):
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

        c.write(get_record1(driver))

    if driver in driver_mode_mingdal['a'] and GDALVersion.runtime() < GDALVersion(
            *driver_mode_mingdal['a'][driver][:2]):
        # Test if driver really can't append for gdal < driver_mode_mingdal

        monkeypatch.delitem(fiona.drvsupport.driver_mode_mingdal['a'], driver)

        with pytest.raises(Exception):
            with fiona.open(path, 'a',
                            driver=driver) as c:
                c.write(get_record2(driver))

            with fiona.open(path) as c:
                assert c.driver == driver
                assert len([f for f in c]) == 2


@pytest.mark.parametrize('driver', [driver for driver, raw in supported_drivers.items() if
                                    raw == 'r' and driver not in blacklist_write_drivers])
def test_no_write_driver_cannot_write(tmpdir, driver, monkeypatch):
    """Test if read only driver cannot write
    
    If this test fails, it should be considered to enable write support for the respective driver in drvsupport.py. 
    
    """

    monkeypatch.setitem(fiona.drvsupport.supported_drivers, driver, 'rw')

    if driver == "BNA" and GDALVersion.runtime() < GDALVersion(2, 0):
        # BNA driver segfaults with gdal 1.11
        return

    path = str(tmpdir.join(get_temp_filename(driver)))

    with pytest.raises(Exception):
        with fiona.open(path, 'w',
                        driver=driver,
                        schema=get_schema(driver)) as c:
            c.write(get_record1(driver))


@pytest.mark.parametrize('driver', [driver for driver, raw in supported_drivers.items() if
                                    'w' in raw and 'a' not in raw and driver not in blacklist_append_drivers])
def test_no_append_driver_cannot_append(tmpdir, driver, monkeypatch):
    """
    Test if a driver that supports write cannot also append

    If this test fails, it should be considered to enable append support for the respective driver in drvsupport.py.

    """

    monkeypatch.setitem(fiona.drvsupport.supported_drivers, driver, 'raw')

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

        c.write(get_record1(driver))

    with pytest.raises(Exception):
        with fiona.open(path, 'a',
                        driver=driver) as c:
            c.write(get_record2(driver))

        with fiona.open(path) as c:
            assert c.driver == driver
            assert len([f for f in c]) == 2


def test_mingdal_drivers_are_supported():
    """
        Test if mode and driver is enabled in supported_drivers
    """

    for mode in driver_mode_mingdal:
        for driver in driver_mode_mingdal[mode]:
            # we cannot test drivers that are not present in the gdal installation
            if driver in supported_drivers:
                assert mode in supported_drivers[driver]
