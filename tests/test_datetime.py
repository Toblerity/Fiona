"""
See also test_rfc3339.py for datetime parser tests.
"""
from collections import OrderedDict

import fiona
import pytest

from fiona.errors import DriverSupportError
from .conftest import get_temp_filename
from fiona.env import GDALVersion
import datetime
from fiona.drvsupport import (supported_drivers, driver_mode_mingdal, driver_converts_field_type_silently_to_str,
                              driver_supports_field, driver_converts_to_str)

gdal_version = GDALVersion.runtime()
drivers_not_supporting_milliseconds = {'GPSTrackMaker'}


def get_schema(driver, field_type):
    if driver == 'GPX':
        return {'properties': OrderedDict([('ele', 'float'),
                                           ('time', field_type)]),
                'geometry': 'Point'}
    if driver == 'GPSTrackMaker':
        return {
            'properties': OrderedDict([('name', 'str'), ('comment', 'str'), ('icon', 'int'), ('time', field_type)]),
            'geometry': 'Point'}

    return {"geometry": "Point",
            "properties": {"datefield": field_type}}


def get_records(driver, values):
    if driver == 'GPX':
        return [{"geometry": {"type": "Point", "coordinates": [1, 2]},
                 "properties": {'ele': 0, "time": val}} for val in values]
    if driver == 'GPSTrackMaker':
        return [{"geometry": {"type": "Point", "coordinates": [1, 2]},
                 "properties": OrderedDict([('name', ''), ('comment', ''), ('icon', 48), ('time', val)])} for
                val in values]

    return [{"geometry": {"type": "Point", "coordinates": [1, 2]},
             "properties": {"datefield": val}} for val in values]


def get_schema_field(driver, schema):
    if driver in {'GPX', 'GPSTrackMaker'}:
        return schema["properties"]["time"]
    return schema["properties"]["datefield"]


def get_field(driver, f):
    if driver in {'GPX', 'GPSTrackMaker'}:
        return f["properties"]["time"]
    return f['properties']['datefield']


def generate_testdata(data_type, driver):
    """ Generate test cases for test_datefield
    Each testcase has the format [(in_value1, out_value1), (in_value2, out_value2), ...]
    """

    # Test data for 'date' data type
    if data_type == 'date' and driver == 'CSV':
        return [("2018-03-25", "2018/03/25"),
                (datetime.date(2018, 3, 25), "2018/03/25"),
                (None, '')]
    elif data_type == 'date' and driver == 'GML':
        if gdal_version < GDALVersion(3, 1):
            return [("2018-03-25", '2018/03/25'),
                    (datetime.date(2018, 3, 25), '2018/03/25'),
                    (None, None)]
        else:
            return [("2018-03-25", "2018-03-25"),
                    (datetime.date(2018, 3, 25), "2018-03-25"),
                    (None, None)]
    elif data_type == 'date' and ((driver == 'GeoJSON' and gdal_version.major < 2) or
                                  (driver == 'GMT' and gdal_version.major < 2)):
        return [("2018-03-25", "2018/03/25"),
                (datetime.date(2018, 3, 25), "2018/03/25"),
                (None, None)]
    if data_type == 'date' and driver == 'PCIDSK':
        if gdal_version < GDALVersion(2, 1):
            return [("2018-03-25", ''),
                    (datetime.date(2018, 3, 25), ''),
                    (None, '')]
        else:
            return [("2018-03-25", "2018/03/25 00:00:00"),
                    (datetime.date(2018, 3, 25), "2018/03/25 00:00:00"),
                    (None, '')]
    elif data_type == 'date':
        return [("2018-03-25", "2018-03-25"),
                (datetime.date(2018, 3, 25), "2018-03-25"),
                (None, None)]

    # Test data for 'datetime' data type
    if data_type == 'datetime' and driver == 'PCIDSK':
        if gdal_version < GDALVersion(2, 1):
            return [("2018-03-25T22:49:05", ''),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5), ''),
                    ("2018-03-25T22:49:05.22", ''),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5, 220000), ''),
                    ("2018-03-25T22:49:05.123456", ''),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5, 123456), ''),
                    (None, '')]
        else:
            return [("2018-03-25T22:49:05", "2018/03/25 22:49:05"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5), "2018/03/25 22:49:05"),
                    ("2018-03-25T22:49:05.22", "2018/03/25 22:49:05.220"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5, 220000), "2018/03/25 22:49:05.220"),
                    ("2018-03-25T22:49:05.123456", "2018/03/25 22:49:05.123"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5, 123456), "2018/03/25 22:49:05.123"),
                    (None, '')]
    elif data_type == 'datetime' and driver == 'GML':
        if gdal_version.major < 2:
            return [("2018-03-25T22:49:05", "2018/03/25 22:49:05"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5), "2018/03/25 22:49:05"),
                    ("2018-03-25T22:49:05.22", "2018/03/25 22:49:05"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5, 220000), "2018/03/25 22:49:05"),
                    ("2018-03-25T22:49:05.123456", "2018/03/25 22:49:05"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5, 123456), "2018/03/25 22:49:05"),
                    (None, None)]
        elif gdal_version.major >= 2 and gdal_version < GDALVersion(3, 1):
            return [("2018-03-25T22:49:05", "2018/03/25 22:49:05"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5), "2018/03/25 22:49:05"),
                    ("2018-03-25T22:49:05.22", "2018/03/25 22:49:05.220"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5, 220000), "2018/03/25 22:49:05.220"),
                    ("2018-03-25T22:49:05.123456", "2018/03/25 22:49:05.123"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5, 123456), "2018/03/25 22:49:05.123"),
                    (None, None)]
        else:
            return [("2018-03-25T22:49:05", "2018-03-25T22:49:05"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5), "2018-03-25T22:49:05"),
                    ("2018-03-25T22:49:05.22", "2018-03-25T22:49:05.220000"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5, 220000), "2018-03-25T22:49:05.220000"),
                    ("2018-03-25T22:49:05.123456", "2018-03-25T22:49:05.123000"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5, 123456), "2018-03-25T22:49:05.123000"),
                    (None, None)]
    elif data_type == 'datetime' and driver == 'GPSTrackMaker':
        return [("2018-03-25T22:49:05", "2018-03-25T22:49:05"),
                (datetime.datetime(2018, 3, 25, 22, 49, 5), "2018-03-25T22:49:05"),
                ("2018-03-25T22:49:05.22", "2018-03-25T22:49:05"),
                (datetime.datetime(2018, 3, 25, 22, 49, 5, 220000), "2018-03-25T22:49:05"),
                ("2018-03-25T22:49:05.123456", "2018-03-25T22:49:05"),
                (datetime.datetime(2018, 3, 25, 22, 49, 5, 123456), "2018-03-25T22:49:05"),
                (None, None)]
    elif data_type == 'datetime' and driver == 'CSV':
        if gdal_version.major < 2:
            return [("2018-03-25T22:49:05", "2018/03/25 22:49:05"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5), "2018/03/25 22:49:05"),
                    ("2018-03-25T22:49:05.22", "2018/03/25 22:49:05"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5, 220000), "2018/03/25 22:49:05"),
                    ("2018-03-25T22:49:05.123456", "2018/03/25 22:49:05"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5, 123456), "2018/03/25 22:49:05"),
                    (None, '')]
        else:
            return [("2018-03-25T22:49:05", "2018/03/25 22:49:05"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5), "2018/03/25 22:49:05"),
                    ("2018-03-25T22:49:05.22", "2018/03/25 22:49:05.220"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5, 220000), "2018/03/25 22:49:05.220"),
                    ("2018-03-25T22:49:05.123456", "2018/03/25 22:49:05.123"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5, 123456), "2018/03/25 22:49:05.123"),
                    (None, '')]
    if data_type == 'datetime' and driver == 'GeoJSON' and gdal_version.major < 2:
        return [("2018-03-25T22:49:05", "2018/03/25 22:49:05"),
                (datetime.datetime(2018, 3, 25, 22, 49, 5), "2018/03/25 22:49:05"),
                ("2018-03-25T22:49:05.22", "2018/03/25 22:49:05"),
                (datetime.datetime(2018, 3, 25, 22, 49, 5, 220000), "2018/03/25 22:49:05"),
                ("2018-03-25T22:49:05.123456", "2018/03/25 22:49:05"),
                (datetime.datetime(2018, 3, 25, 22, 49, 5, 123456), "2018/03/25 22:49:05"),
                (None, None)]
    elif data_type == 'datetime':
        if gdal_version.major < 2:
            return [("2018-03-25T22:49:05", "2018-03-25T22:49:05"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5), "2018-03-25T22:49:05"),
                    ("2018-03-25T22:49:05.22", "2018-03-25T22:49:05"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5, 220000), "2018-03-25T22:49:05"),
                    ("2018-03-25T22:49:05.123456", "2018-03-25T22:49:05"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5, 123456), "2018-03-25T22:49:05"),
                    (None, None)]
        else:
            return [("2018-03-25T22:49:05", "2018-03-25T22:49:05"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5), "2018-03-25T22:49:05"),
                    ("2018-03-25T22:49:05.22", "2018-03-25T22:49:05.220000"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5, 220000), "2018-03-25T22:49:05.220000"),
                    ("2018-03-25T22:49:05.123456", "2018-03-25T22:49:05.123000"),
                    (datetime.datetime(2018, 3, 25, 22, 49, 5, 123456), "2018-03-25T22:49:05.123000"),
                    (None, None)]

    # Test data for 'time' data type
    if data_type == 'time' and driver == 'PCIDSK':
        if gdal_version < GDALVersion(2, 1):
            return [("22:49:05", ''),
                    (datetime.time(22, 49, 5), ''),
                    ("22:49:05.22", ''),
                    (datetime.time(22, 49, 5, 220000), ''),
                    ("22:49:05.123456", ''),
                    (datetime.time(22, 49, 5, 123456), ''),
                    (None, '')]
        else:
            return [("22:49:05", '0000/00/00 22:49:05'),
                    (datetime.time(22, 49, 5), '0000/00/00 22:49:05'),
                    ("22:49:05.22", '0000/00/00 22:49:05.220'),
                    (datetime.time(22, 49, 5, 220000), '0000/00/00 22:49:05.220'),
                    ("22:49:05.123456", '0000/00/00 22:49:05.123'),
                    (datetime.time(22, 49, 5, 123456), '0000/00/00 22:49:05.123'),
                    (None, '')]
    elif data_type == 'time' and driver == 'GPKG' and gdal_version >= GDALVersion(2, 0):
        return [("22:49:05", "22:49:05"),
                (datetime.time(22, 49, 5), "22:49:05"),
                ("22:49:05.22", "22:49:05.220"),
                (datetime.time(22, 49, 5, 220000), "22:49:05.220"),
                ("22:49:05.123456", "22:49:05.123"),
                (datetime.time(22, 49, 5, 123456), "22:49:05.123"),
                (None, None)]
    elif data_type == 'time' and driver == 'MapInfo File':
        if gdal_version.major < 2:
            return [("22:49:05", "22:49:05"),
                    (datetime.time(22, 49, 5), "22:49:05"),
                    ("22:49:05.22", "22:49:05"),
                    (datetime.time(22, 49, 5, 220000), "22:49:05"),
                    ("22:49:05.123456", "22:49:05"),
                    (datetime.time(22, 49, 5, 123456), "22:49:05"),
                    (None, None)]
        else:
            return [("22:49:05", "22:49:05"),
                    (datetime.time(22, 49, 5), "22:49:05"),
                    ("22:49:05.22", "22:49:05.220000"),
                    (datetime.time(22, 49, 5, 220000), "22:49:05.220000"),
                    ("22:49:05.123456", "22:49:05.123000"),
                    (datetime.time(22, 49, 5, 123456), "22:49:05.123000"),
                    (None, '00:00:00')]
    elif data_type == 'time' and driver == 'CSV':
        if gdal_version.major < 2:
            return [("22:49:05", "22:49:05"),
                    (datetime.time(22, 49, 5), "22:49:05"),
                    ("22:49:05.22", "22:49:05"),
                    (datetime.time(22, 49, 5, 220000), "22:49:05"),
                    ("22:49:05.123456", "22:49:05"),
                    (datetime.time(22, 49, 5, 123456), "22:49:05"),
                    (None, '')]
        else:
            return [("22:49:05", "22:49:05"),
                    (datetime.time(22, 49, 5), "22:49:05"),
                    ("22:49:05.22", "22:49:05.220"),
                    (datetime.time(22, 49, 5, 220000), "22:49:05.220"),
                    ("22:49:05.123456", "22:49:05.123"),
                    (datetime.time(22, 49, 5, 123456), "22:49:05.123"),
                    (None, '')]
    elif data_type == 'time' and driver in {'GeoJSON', 'GeoJSONSeq'}:
        if gdal_version.major < 2:
            return [("22:49:05", "22:49:05"),
                    (datetime.time(22, 49, 5), "22:49:05"),
                    ("22:49:05.22", "22:49:05"),
                    (datetime.time(22, 49, 5, 220000), "22:49:05"),
                    ("22:49:05.123456", "22:49:05"),
                    (datetime.time(22, 49, 5, 123456), "22:49:05"),
                    (None, None)]
        else:
            return [("22:49:05", "22:49:05"),
                    (datetime.time(22, 49, 5), "22:49:05"),
                    ("22:49:05.22", "22:49:05.220000"),
                    (datetime.time(22, 49, 5, 220000), "22:49:05.220000"),
                    ("22:49:05.123456", "22:49:05.123000"),
                    (datetime.time(22, 49, 5, 123456), "22:49:05.123000"),
                    (None, None)]
    elif data_type == 'time':
        if gdal_version.major < 2:
            return [("22:49:05", "22:49:05"),
                    (datetime.time(22, 49, 5), "22:49:05"),
                    ("22:49:05.22", "22:49:05"),
                    (datetime.time(22, 49, 5, 220000), "22:49:05"),
                    ("22:49:05.123456", "22:49:05"),
                    (datetime.time(22, 49, 5, 123456), "22:49:05"),
                    (None, None)]
        else:
            return [("22:49:05", "22:49:05"),
                    (datetime.time(22, 49, 5), "22:49:05"),
                    ("22:49:05.22", "22:49:05.220000"),
                    (datetime.time(22, 49, 5, 220000), "22:49:05.220000"),
                    ("22:49:05.123456", "22:49:05.123000"),
                    (datetime.time(22, 49, 5, 123456), "22:49:05.123000"),
                    (None, None)]


@pytest.mark.parametrize("driver", [driver for driver, raw in supported_drivers.items() if 'w' in raw
                                    and (driver not in driver_mode_mingdal['w'] or
                                         gdal_version >= GDALVersion(*driver_mode_mingdal['w'][driver][:2]))])
@pytest.mark.parametrize("field_type", ['date', 'datetime', 'time'])
def test_datefield(tmpdir, driver, field_type):
    """
    Test handling of date, time, datetime types for write capable drivers
    """

    schema = get_schema(driver, field_type)
    path = str(tmpdir.join(get_temp_filename(driver)))
    # Some driver do not support date, datetime or time
    if not driver_supports_field(driver, field_type):
        with pytest.raises(DriverSupportError):
            with fiona.open(path, 'w',
                            driver=driver,
                            schema=schema) as c:
                pass

    else:
        values_in, values_out = zip(*generate_testdata(field_type, driver))
        records = get_records(driver, values_in)

        # Some driver silently convert date / datetime / time to str
        if driver_converts_field_type_silently_to_str(driver, field_type):
            with pytest.warns(UserWarning) as record:
                with fiona.open(path, 'w',
                                driver=driver,
                                schema=schema) as c:
                    c.writerecords(records)
                assert len(record) == 1
                assert "silently converts" in record[0].message.args[0]

            with fiona.open(path, 'r') as c:
                assert get_schema_field(driver, c.schema) == 'str'
                items = [get_field(driver, f) for f in c]
                assert len(items) == len(values_in)
                for val_in, val_out in zip(items, values_out):
                    assert val_in == val_out

        else:
            with fiona.open(path, 'w',
                            driver=driver,
                            schema=schema) as c:
                c.writerecords(records)

            with fiona.open(path, 'r') as c:
                assert get_schema_field(driver, c.schema) == field_type
                items = [get_field(driver, f) for f in c]
                assert len(items) == len(values_in)
                for val_in, val_out in zip(items, values_out):
                    assert val_in == val_out


@pytest.mark.parametrize("driver", [driver for driver, raw in supported_drivers.items() if 'w' in raw
                                    and (driver not in driver_mode_mingdal['w'] or
                                         gdal_version >= GDALVersion(*driver_mode_mingdal['w'][driver][:2]))])
@pytest.mark.parametrize("field_type", ['date', 'datetime', 'time'])
def test_datetime_field_type_marked_not_supported_is_not_supported(tmpdir, driver, field_type, monkeypatch):
    """ Test if a date/datetime/time field type marked as not not supported is really not supported

    Warning: Success of this test does not necessary mean that a field is not supported. E.g. errors can occour due to
    special schema requirements of drivers. This test only covers the standard case.

    """

    if driver == "BNA" and gdal_version < GDALVersion(2, 0):
        # BNA driver segfaults with gdal 1.11
        return

    # If the driver supports the field we have nothing to do here
    if driver_supports_field(driver, field_type):
        return

    monkeypatch.delitem(fiona.drvsupport.driver_field_type_unsupported[field_type], driver)

    schema = get_schema(driver, field_type)
    path = str(tmpdir.join(get_temp_filename(driver)))
    values_in, values_out = zip(*generate_testdata(field_type, driver))
    records = get_records(driver, values_in)

    is_good = True
    try:
        with fiona.open(path, 'w',
                        driver=driver,
                        schema=schema) as c:
            c.writerecords(records)

        with fiona.open(path, 'r') as c:
            if not get_schema_field(driver, c.schema) == field_type:
                is_good = False
            items = [get_field(driver, f) for f in c]
            for val_in, val_out in zip(items, values_out):
                if not val_in == val_out:
                    is_good = False
    except:
        is_good = False
    assert not is_good


def generate_tostr_testcases():
    """ Flatten driver_converts_to_str to a list of (field_type, driver) tuples"""
    cases = []
    for field_type in driver_converts_to_str:
        for driver in driver_converts_to_str[field_type]:
            driver_supported = driver in supported_drivers
            driver_can_write = (driver not in driver_mode_mingdal['w'] or
                                gdal_version >= GDALVersion(*driver_mode_mingdal['w'][driver][:2]))
            field_supported = driver_supports_field(driver, field_type)
            converts_to_str = driver_converts_field_type_silently_to_str(driver, field_type)
            if driver_supported and driver_can_write and converts_to_str and field_supported:
                cases.append((field_type, driver))
    return cases


@pytest.mark.parametrize("field_type,driver", generate_tostr_testcases())
def test_driver_marked_as_silently_converts_to_str_converts_silently_to_str(tmpdir, driver, field_type, monkeypatch):
    """ Test if a driver and field_type is marked in fiona.drvsupport.driver_converts_to_str to convert to str really
      silently converts to str

      If this test fails, it should be considered to replace the respective None value in
      fiona.drvsupport.driver_converts_to_str with a GDALVersion(major, minor) value.
      """

    monkeypatch.delitem(fiona.drvsupport.driver_converts_to_str[field_type], driver)

    schema = get_schema(driver, field_type)
    path = str(tmpdir.join(get_temp_filename(driver)))
    values_in, values_out = zip(*generate_testdata(field_type, driver))
    records = get_records(driver, values_in)

    with fiona.open(path, 'w',
                    driver=driver,
                    schema=schema) as c:
        c.writerecords(records)

    with fiona.open(path, 'r') as c:
        assert get_schema_field(driver, c.schema) == 'str'
