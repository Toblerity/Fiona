"""
See also test_rfc3339.py for datetime parser tests.
"""

import fiona
import pytest
import tempfile, shutil
import os
from fiona.errors import DriverSupportError
from .conftest import requires_gpkg

GDAL_MAJOR_VER = fiona.get_gdal_version_num() // 1000000

GEOMETRY_TYPE = "Point"
GEOMETRY_EXAMPLE = {"type": "Point", "coordinates": [1, 2]}

DRIVER_FILENAME = {
    "ESRI Shapefile": "test.shp",
    "GPKG": "test.gpkg",
    "GeoJSON": "test.geojson",
    "MapInfo File": "test.tab",
}

DATE_EXAMPLE = "2018-03-25"
DATETIME_EXAMPLE = "2018-03-25T22:49:05"
TIME_EXAMPLE = "22:49:05"

class TestDateFieldSupport:
    def write_data(self, driver):
        filename = DRIVER_FILENAME[driver]
        temp_dir = tempfile.mkdtemp()
        path = os.path.join(temp_dir, filename)
        schema = {
            "geometry": GEOMETRY_TYPE,
            "properties": {
                "date": "date",
            }
        }
        records = [
            {
                "geometry": GEOMETRY_EXAMPLE,
                "properties": {
                    "date": DATE_EXAMPLE,
                }
            },
            {
                "geometry": GEOMETRY_EXAMPLE,
                "properties": {
                    "date": None,
                }
            },
        ]
        with fiona.Env(), fiona.open(path, "w", driver=driver, schema=schema) as collection:
            collection.writerecords(records)

        with fiona.Env(), fiona.open(path, "r") as collection:
            schema = collection.schema
            features = list(collection)

        shutil.rmtree(temp_dir)

        return schema, features

    def test_shapefile(self):
        driver = "ESRI Shapefile"
        schema, features = self.write_data(driver)

        assert schema["properties"]["date"] == "date"
        assert features[0]["properties"]["date"] == DATE_EXAMPLE
        assert features[1]["properties"]["date"] is None

    @requires_gpkg
    def test_gpkg(self):
        driver = "GPKG"
        schema, features = self.write_data(driver)

        assert schema["properties"]["date"] == "date"
        assert features[0]["properties"]["date"] == DATE_EXAMPLE
        assert features[1]["properties"]["date"] is None

    def test_geojson(self):
        # GDAL 1: date field silently converted to string
        # GDAL 1: date string format uses / instead of -
        driver = "GeoJSON"
        schema, features = self.write_data(driver)

        if GDAL_MAJOR_VER >= 2:
            assert schema["properties"]["date"] == "date"
            assert features[0]["properties"]["date"] == DATE_EXAMPLE
        else:
            assert schema["properties"]["date"] == "str"
            assert features[0]["properties"]["date"] == "2018/03/25"
        assert features[1]["properties"]["date"] is None

    def test_mapinfo(self):
        driver = "MapInfo File"
        schema, features = self.write_data(driver)

        assert schema["properties"]["date"] == "date"
        assert features[0]["properties"]["date"] == DATE_EXAMPLE
        assert features[1]["properties"]["date"] is None


class TestDatetimeFieldSupport:
    def write_data(self, driver):
        filename = DRIVER_FILENAME[driver]
        temp_dir = tempfile.mkdtemp()
        path = os.path.join(temp_dir, filename)
        schema = {
            "geometry": GEOMETRY_TYPE,
            "properties": {
                "datetime": "datetime",
            }
        }
        records = [
            {
                "geometry": GEOMETRY_EXAMPLE,
                "properties": {
                    "datetime": DATETIME_EXAMPLE,
                }
            },
            {
                "geometry": GEOMETRY_EXAMPLE,
                "properties": {
                    "datetime": None,
                }
            },
        ]
        with fiona.Env(), fiona.open(path, "w", driver=driver, schema=schema) as collection:
            collection.writerecords(records)

        with fiona.Env(), fiona.open(path, "r") as collection:
            schema = collection.schema
            features = list(collection)

        shutil.rmtree(temp_dir)

        return schema, features

    def test_shapefile(self):
        # datetime is silently converted to date
        driver = "ESRI Shapefile"

        with pytest.raises(DriverSupportError):
            schema, features = self.write_data(driver)

        # assert schema["properties"]["datetime"] == "date"
        # assert features[0]["properties"]["datetime"] == "2018-03-25"
        # assert features[1]["properties"]["datetime"] is None

    @requires_gpkg
    def test_gpkg(self):
        # GDAL 1: datetime silently downgraded to date
        driver = "GPKG"

        if GDAL_MAJOR_VER >= 2:
            schema, features = self.write_data(driver)
            assert schema["properties"]["datetime"] == "datetime"
            assert features[0]["properties"]["datetime"] == DATETIME_EXAMPLE
            assert features[1]["properties"]["datetime"] is None
        else:
            with pytest.raises(DriverSupportError):
                schema, features = self.write_data(driver)

    def test_geojson(self):
        # GDAL 1: datetime silently converted to string
        # GDAL 1: date string format uses / instead of -
        driver = "GeoJSON"
        schema, features = self.write_data(driver)

        if GDAL_MAJOR_VER >= 2:
            assert schema["properties"]["datetime"] == "datetime"
            assert features[0]["properties"]["datetime"] == DATETIME_EXAMPLE
        else:
            assert schema["properties"]["datetime"] == "str"
            assert features[0]["properties"]["datetime"] == "2018/03/25 22:49:05"
        assert features[1]["properties"]["datetime"] is None

    def test_mapinfo(self):
        driver = "MapInfo File"
        schema, features = self.write_data(driver)

        assert schema["properties"]["datetime"] == "datetime"
        assert features[0]["properties"]["datetime"] == DATETIME_EXAMPLE
        assert features[1]["properties"]["datetime"] is None


class TestTimeFieldSupport:
    def write_data(self, driver):
        filename = DRIVER_FILENAME[driver]
        temp_dir = tempfile.mkdtemp()
        path = os.path.join(temp_dir, filename)
        schema = {
            "geometry": GEOMETRY_TYPE,
            "properties": {
                "time": "time",
            }
        }
        records = [
            {
                "geometry": GEOMETRY_EXAMPLE,
                "properties": {
                    "time": TIME_EXAMPLE,
                }
            },
            {
                "geometry": GEOMETRY_EXAMPLE,
                "properties": {
                    "time": None,
                }
            },
        ]
        with fiona.Env(), fiona.open(path, "w", driver=driver, schema=schema) as collection:
            collection.writerecords(records)

        with fiona.Env(), fiona.open(path, "r") as collection:
            schema = collection.schema
            features = list(collection)

        shutil.rmtree(temp_dir)

        return schema, features

    def test_shapefile(self):
        # no support for time fields
        driver = "ESRI Shapefile"
        with pytest.raises(DriverSupportError):
            self.write_data(driver)

    @requires_gpkg
    def test_gpkg(self):
        # GDAL 2: time field is silently converted to string
        # GDAL 1: time field dropped completely
        driver = "GPKG"

        with pytest.raises(DriverSupportError):
            schema, features = self.write_data(driver)

        # if GDAL_MAJOR_VER >= 2:
        #     assert schema["properties"]["time"] == "str"
        #     assert features[0]["properties"]["time"] == TIME_EXAMPLE
        #     assert features[1]["properties"]["time"] is None
        # else:
        #     assert "time" not in schema["properties"]

    def test_geojson(self):
        # GDAL 1: time field silently converted to string
        driver = "GeoJSON"
        schema, features = self.write_data(driver)

        if GDAL_MAJOR_VER >= 2:
            assert schema["properties"]["time"] == "time"
        else:
            assert schema["properties"]["time"] == "str"
        assert features[0]["properties"]["time"] == TIME_EXAMPLE
        assert features[1]["properties"]["time"] is None

    def test_mapinfo(self):
        # GDAL 2: null time is converted to 00:00:00 (regression?)
        driver = "MapInfo File"
        schema, features = self.write_data(driver)

        assert schema["properties"]["time"] == "time"
        assert features[0]["properties"]["time"] == TIME_EXAMPLE
        if GDAL_MAJOR_VER >= 2:
            assert features[1]["properties"]["time"] == "00:00:00"
        else:
            assert features[1]["properties"]["time"] is None
