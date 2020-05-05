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
from fiona.drvsupport import supported_drivers, driver_mode_mingdal, driver_converts_field_type_silently_to_str

gdal_version = GDALVersion.runtime()


def generate_testdata(data_type, driver):
    """ Generate test cases for test_datefield

    Each test case has the format [(in_value1, out_value1), (in_value2, out_value2), ...]
    """

    # Test data for 'date' data type
    if data_type == 'date':
        return [("2018-03-25", "2018-03-25"),
                (datetime.date(2018, 3, 25), "2018-03-25"),
                (None, None)]

    # Test data for 'datetime' data type
    if data_type == 'datetime':
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
    if data_type == 'time' and driver == 'MapInfo File' and gdal_version.major > 1:
        return [("22:49:05", "22:49:05"),
                (datetime.time(22, 49, 5), "22:49:05"),
                ("22:49:05.22", "22:49:05.220000"),
                (datetime.time(22, 49, 5, 220000), "22:49:05.220000"),
                ("22:49:05.123456", "22:49:05.123000"),
                (datetime.time(22, 49, 5, 123456), "22:49:05.123000"),
                (None, '00:00:00')]
    elif data_type == 'time' and driver in {'GeoJSON', 'GeoJSONSeq'}:
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
                    ("22:49:05.22", "22:49:05.220"),
                    (datetime.time(22, 49, 5, 220000), "22:49:05.220"),
                    ("22:49:05.123456", "22:49:05.123000"),
                    (datetime.time(22, 49, 5, 123456), "22:49:05.123000"),
                    (None, None)]


# DGN: DGN schema contains no date/time fields
# BNA: It only contains geometry and a few identifiers per record. Attributes must be stored into external files.
# DXF: DXF schema contains no date/time fields
@pytest.mark.parametrize("driver", [driver for driver, raw in supported_drivers.items() if 'w' in raw
                                    and (driver not in driver_mode_mingdal['w'] or
                                         gdal_version >= GDALVersion(*driver_mode_mingdal['w'][driver][:2]))
                                    and driver not in {'DGN', 'BNA', 'DXF'}])
@pytest.mark.parametrize("data_type", ['date', 'datetime', 'time'])
def test_datefield(tmpdir, driver, data_type):
    """
    Test handling of date, time, datetime types for write capable drivers
    """

    def get_schema():

        if driver == 'GPX':
            return {'properties': OrderedDict([('ele', 'float'),
                                               ('time', data_type)]),
                    'geometry': 'Point'}
        if driver == 'GPSTrackMaker':
            return {'properties': OrderedDict([('time', data_type)]),
                    'geometry': 'Point'}

        return {"geometry": "Point",
                "properties": {"datefield": data_type}}

    schema = get_schema()
    print(schema)

    def get_records(values):
        if driver == 'GPX':
            return [{"geometry": {"type": "Point", "coordinates": [1, 2]},
                     "properties": {'ele': 0, "time": val}} for val in values]
        if driver == 'GPSTrackMaker':
            return [{"geometry": {"type": "Point", "coordinates": [1, 2]},
                     "properties": {"time": val}} for val in values]

        return [{"geometry": {"type": "Point", "coordinates": [1, 2]},
                 "properties": {"datefield": val}} for val in values]

    def get_schema_field(schema):
        if driver in {'GPX', 'GPSTrackMaker'}:
            return schema["properties"]["time"]
        return schema["properties"]["datefield"]

    def get_field(f):
        if driver in {'GPX', 'GPSTrackMaker'}:
            return f["properties"]["time"]
        return f['properties']['datefield']

    path = str(tmpdir.join(get_temp_filename(driver)))

    # Some driver do not support date, datetime or time
    if ((driver == 'ESRI Shapefile' and data_type in {'datetime', 'time'}) or
            (driver == 'GPKG' and data_type == 'time') or
            (driver == 'GPKG' and gdal_version.major < 2 and data_type in {'datetime', 'time'}) or
            (driver == 'GML' and data_type == 'time' and gdal_version < GDALVersion(3, 1))):
        with pytest.raises(DriverSupportError):
            with fiona.open(path, 'w',
                            driver=driver,
                            schema=schema) as c:
                pass

    else:
        values_in, values_out = zip(*generate_testdata(data_type, driver))
        records = get_records(values_in)

        # Some driver silently convert date / datetime / time to str
        if driver_converts_field_type_silently_to_str(driver, data_type):
            with pytest.warns(UserWarning) as record:
                with fiona.open(path, 'w',
                                driver=driver,
                                schema=schema) as c:
                    c.writerecords(records)
                assert len(record) == 1
                assert "silently converts" in record[0].message.args[0]

            with fiona.open(path, 'r') as c:
                assert get_schema_field(c.schema) == 'str'

        else:
            with fiona.open(path, 'w',
                            driver=driver,
                            schema=schema) as c:
                c.writerecords(records)

            with fiona.open(path, 'r') as c:
                # GPX and GPSTrackMaker convert time and date to datetime
                if driver in {'GPX', 'GPSTrackMaker'}:
                    assert get_schema_field(c.schema) == 'datetime'
                else:
                    assert get_schema_field(c.schema) == data_type

                    items = [get_field(f) for f in c]

                    assert len(items) == len(values_in)
                    for val_in, val_out in zip(items, values_out):
                        assert val_in == val_out
