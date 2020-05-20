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
    special_schemas = {'CSV': {'geometry': None, 'properties': OrderedDict([('position', 'int')])},
                       'BNA': {'geometry': 'Point', 'properties': {}},
                       'DXF': {'properties': OrderedDict(
                           [('Layer', 'str'),
                            ('SubClasses', 'str'),
                            ('Linetype', 'str'),
                            ('EntityHandle', 'str'),
                            ('Text', 'str')]),
                           'geometry': 'Point'},
                       'GPX': {'geometry': 'Point',
                               'properties': OrderedDict([('ele', 'float'), ('time', 'datetime')])},
                       'GPSTrackMaker': {'properties': OrderedDict([]), 'geometry': 'Point'},
                       'DGN': {'properties': OrderedDict([]), 'geometry': 'LineString'},
                       'MapInfo File': {'geometry': 'Point', 'properties': OrderedDict([('position', 'str')])}
                       }

    return special_schemas.get(driver, {'geometry': 'Point', 'properties': OrderedDict([('position', 'int')])})


def get_records(driver, range):
    special_records1 = {'CSV': [{'geometry': None, 'properties': {'position': i}} for i in range],
                        'BNA': [{'geometry': {'type': 'Point', 'coordinates': (0.0, float(i))}, 'properties': {}} for i
                                in range],
                        'DXF': [
                            {'geometry': {'type': 'Point', 'coordinates': (0.0, float(i))}, 'properties': OrderedDict(
                                [('Layer', '0'),
                                 ('SubClasses', 'AcDbEntity:AcDbPoint'),
                                 ('Linetype', None),
                                 ('EntityHandle', '20000'),
                                 ('Text', None)])} for i in range],
                        'GPX': [{'geometry': {'type': 'Point', 'coordinates': (0.0, float(i))},
                                 'properties': {'ele': 0.0, 'time': '2020-03-24T16:08:40'}} for i
                                in range],
                        'GPSTrackMaker': [{'geometry': {'type': 'Point', 'coordinates': (0.0, float(i))},
                                           'properties': {}} for i in range],
                        'DGN': [
                            {'geometry': {'type': 'LineString', 'coordinates': [(float(i), 0.0), (0.0, 0.0)]},
                             'properties': {}} for i in range],
                        'MapInfo File': [
                            {'geometry': {'type': 'Point', 'coordinates': (0.0, float(i))},
                             'properties': {'position': str(i)}} for i in range],
                        }
    return special_records1.get(driver, [
        {'geometry': {'type': 'Point', 'coordinates': (0.0, float(i))}, 'properties': {'position': i}} for i in
        range])


def get_records2(driver, range):
    special_records2 = {'DGN': [
        {'geometry': {'type': 'LineString', 'coordinates': [(float(i), 0.0), (0.0, 0.0)]},
         'properties': OrderedDict(
             [('Type', 3),
              ('Level', 0),
              ('GraphicGroup', 0),
              ('ColorIndex', 0),
              ('Weight', 0),
              ('Style', 0),
              ('EntityNum', None),
              ('MSLink', None),
              ('Text', None)])} for i in range],
    }
    return special_records2.get(driver, get_records(driver, range))


def get_pos(f, driver):
    if driver in {'DXF', 'BNA', 'GPX', 'GPSTrackMaker'}:
        return f['geometry']['coordinates'][1]
    elif driver == 'DGN':
        return f['geometry']['coordinates'][0][0]
    else:
        return f['properties']['position']


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

    positions = list(range(0, 10))
    path = str(tmpdir.join(get_temp_filename(driver)))

    if driver in driver_mode_mingdal['w'] and GDALVersion.runtime() < GDALVersion(
            *driver_mode_mingdal['w'][driver][:2]):

        # Test if DriverError is raised for gdal < driver_mode_mingdal
        with pytest.raises(DriverError):
            with fiona.open(path, 'w',
                            driver=driver,
                            schema=get_schema(driver)) as c:
                c.writerecords(get_records(driver, positions))

    else:

        # Test if we can write
        with fiona.open(path, 'w',
                        driver=driver,
                        schema=get_schema(driver)) as c:

            c.writerecords(get_records(driver, positions))

        with fiona.open(path) as c:
            assert c.driver == driver
            items = list(c)
            assert len(items) == len(positions)
            for val_in, val_out in zip(positions, items):
                assert val_in == int(get_pos(val_out, driver))


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

    positions = list(range(0, 10))
    path = str(tmpdir.join(get_temp_filename(driver)))

    if driver in driver_mode_mingdal['w'] and GDALVersion.runtime() < GDALVersion(
            *driver_mode_mingdal['w'][driver][:2]):
        monkeypatch.delitem(fiona.drvsupport.driver_mode_mingdal['w'], driver)

        with pytest.raises(Exception):
            with fiona.open(path, 'w',
                            driver=driver,
                            schema=get_schema(driver)) as c:
                c.writerecords(get_records(driver, positions))


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
    range1 = list(range(0, 5))
    range2 = list(range(5, 10))
    records1 = get_records(driver, range1)
    records2 = get_records2(driver, range2)
    positions = range1 + range2

    # If driver is not able to write, we cannot test append
    if driver in driver_mode_mingdal['w'] and GDALVersion.runtime() < GDALVersion(
            *driver_mode_mingdal['w'][driver][:2]):
        return

    # Create test file to append to
    with fiona.open(path, 'w',
                    driver=driver,
                    schema=get_schema(driver)) as c:

        c.writerecords(records1)

    if driver in driver_mode_mingdal['a'] and GDALVersion.runtime() < GDALVersion(
            *driver_mode_mingdal['a'][driver][:2]):

        # Test if DriverError is raised for gdal < driver_mode_mingdal
        with pytest.raises(DriverError):
            with fiona.open(path, 'a',
                            driver=driver) as c:
                c.writerecords(records2)

    else:
        # Test if we can append
        with fiona.open(path, 'a',
                        driver=driver) as c:
            c.writerecords(records2)

        with fiona.open(path) as c:
            assert c.driver == driver
            items = list(c)
            assert len(items) == len(positions)
            for val_in, val_out in zip(positions, items):
                assert val_in == int(get_pos(val_out, driver))


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
    range1 = list(range(0, 5))
    range2 = list(range(5, 10))
    records1 = get_records(driver, range1)
    records2 = get_records2(driver, range2)
    positions = range1 + range2

    # If driver is not able to write, we cannot test append
    if driver in driver_mode_mingdal['w'] and GDALVersion.runtime() < GDALVersion(
            *driver_mode_mingdal['w'][driver][:2]):
        return

    # Create test file to append to
    with fiona.open(path, 'w',
                    driver=driver,
                    schema=get_schema(driver)) as c:

        c.writerecords(records1)

    if driver in driver_mode_mingdal['a'] and GDALVersion.runtime() < GDALVersion(
            *driver_mode_mingdal['a'][driver][:2]):
        # Test if driver really can't append for gdal < driver_mode_mingdal

        monkeypatch.delitem(fiona.drvsupport.driver_mode_mingdal['a'], driver)

        with pytest.raises(Exception):
            with fiona.open(path, 'a',
                            driver=driver) as c:
                c.writerecords(records2)

            with fiona.open(path) as c:
                assert c.driver == driver
                items = list(c)
                assert len(items) == len(positions)
                for val_in, val_out in zip(positions, items):
                    assert val_in == int(get_pos(val_out, driver))


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
            c.writerecords(get_records(driver, range(0, 10)))


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
    range1 = list(range(0, 5))
    range2 = list(range(5, 10))
    records1 = get_records(driver, range1)
    records2 = get_records2(driver, range2)
    positions = range1 + range2

    # If driver is not able to write, we cannot test append
    if driver in driver_mode_mingdal['w'] and GDALVersion.runtime() < GDALVersion(
            *driver_mode_mingdal['w'][driver][:2]):
        return

    # Create test file to append to
    with fiona.open(path, 'w',
                    driver=driver,
                    schema=get_schema(driver)) as c:

        c.writerecords(records1)

    with pytest.raises(Exception):
        with fiona.open(path, 'a',
                        driver=driver) as c:
            c.writerecords(records2)

        with fiona.open(path) as c:
            assert c.driver == driver
            items = list(c)
            assert len(items) == len(positions)
            for val_in, val_out in zip(positions, items):
                assert val_in == int(get_pos(val_out, driver))


def test_mingdal_drivers_are_supported():
    """
        Test if mode and driver is enabled in supported_drivers
    """

    for mode in driver_mode_mingdal:
        for driver in driver_mode_mingdal[mode]:
            # we cannot test drivers that are not present in the gdal installation
            if driver in supported_drivers:
                assert mode in supported_drivers[driver]
