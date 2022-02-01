"""Tests of driver support"""

import logging

import pytest

from .conftest import requires_gdal24, get_temp_filename

from fiona.drvsupport import supported_drivers, driver_mode_mingdal
import fiona.drvsupport
from fiona.env import GDALVersion
from fiona._env import calc_gdal_version_num, get_gdal_version_num
from fiona.errors import DriverError

log = logging.getLogger()


@requires_gdal24
@pytest.mark.parametrize("format", ["GeoJSON", "ESRIJSON", "TopoJSON", "GeoJSONSeq"])
def test_geojsonseq(format):
    """Format is available"""
    assert format in fiona.drvsupport.supported_drivers.keys()


@pytest.mark.parametrize(
    "driver", [driver for driver, raw in supported_drivers.items() if "w" in raw]
)
def test_write_or_driver_error(tmpdir, driver, testdata_generator):
    """
    Test if write mode works.

    """

    if driver == "BNA" and GDALVersion.runtime() < GDALVersion(2, 0):
        pytest.skip("BNA driver segfaults with gdal 1.11")

    schema, crs, records1, _, test_equal, create_kwargs = testdata_generator(
        driver, range(0, 10), []
    )
    path = str(tmpdir.join(get_temp_filename(driver)))

    if driver in driver_mode_mingdal[
        "w"
    ] and get_gdal_version_num() < calc_gdal_version_num(
        *driver_mode_mingdal["w"][driver]
    ):

        # Test if DriverError is raised for gdal < driver_mode_mingdal
        with pytest.raises(DriverError):
            with fiona.open(
                path, "w", driver=driver, crs=crs, schema=schema, **create_kwargs
            ) as c:
                c.writerecords(records1)

    else:
        # Test if we can write
        with fiona.open(
            path, "w", driver=driver, crs=crs, schema=schema, **create_kwargs
        ) as c:

            c.writerecords(records1)

        if driver in {"FileGDB", "OpenFileGDB"}:
            open_driver = driver
        else:
            open_driver = None

        with fiona.open(path, driver=open_driver) as collection:
            assert collection.driver == driver
            assert len(list(collection)) == len(records1)


@pytest.mark.parametrize(
    "driver", [driver for driver in driver_mode_mingdal["w"].keys()]
)
def test_write_does_not_work_when_gdal_smaller_mingdal(
    tmpdir, driver, testdata_generator, monkeypatch
):
    """
    Test if driver really can't write for gdal < driver_mode_mingdal

    If this test fails, it should be considered to update driver_mode_mingdal in drvsupport.py.

    """

    if driver == "BNA" and GDALVersion.runtime() < GDALVersion(2, 0):
        pytest.skip("BNA driver segfaults with gdal 1.11")
    if driver == "FlatGeobuf" and calc_gdal_version_num(
        3, 1, 0
    ) <= get_gdal_version_num() < calc_gdal_version_num(3, 1, 3):
        pytest.skip("See https://github.com/Toblerity/Fiona/pull/924")

    schema, crs, records1, _, test_equal, create_kwargs = testdata_generator(
        driver, range(0, 10), []
    )
    path = str(tmpdir.join(get_temp_filename(driver)))

    if driver in driver_mode_mingdal[
        "w"
    ] and get_gdal_version_num() < calc_gdal_version_num(
        *driver_mode_mingdal["w"][driver]
    ):
        monkeypatch.delitem(fiona.drvsupport.driver_mode_mingdal["w"], driver)

        with pytest.raises(Exception):
            with fiona.open(
                path, "w", driver=driver, crs=crs, schema=schema, **create_kwargs
            ) as c:
                c.writerecords(records1)


@pytest.mark.parametrize(
    "driver", [driver for driver, raw in supported_drivers.items() if "a" in raw]
)
def test_append_or_driver_error(tmpdir, testdata_generator, driver):
    """Test if driver supports append mode.

    Some driver only allow a specific schema. These drivers can be excluded by adding them to blacklist_append_drivers.

    """
    if driver == "DGN":
        pytest.xfail("DGN schema has changed")

    if driver == "BNA" and GDALVersion.runtime() < GDALVersion(2, 0):
        pytest.skip("BNA driver segfaults with gdal 1.11")

    path = str(tmpdir.join(get_temp_filename(driver)))
    schema, crs, records1, records2, test_equal, create_kwargs = testdata_generator(
        driver, range(0, 5), range(5, 10)
    )

    # If driver is not able to write, we cannot test append
    if driver in driver_mode_mingdal[
        "w"
    ] and get_gdal_version_num() < calc_gdal_version_num(
        *driver_mode_mingdal["w"][driver]
    ):
        return

    # Create test file to append to
    with fiona.open(
        path, "w", driver=driver, crs=crs, schema=schema, **create_kwargs
    ) as c:

        c.writerecords(records1)

    if driver in driver_mode_mingdal[
        "a"
    ] and get_gdal_version_num() < calc_gdal_version_num(
        *driver_mode_mingdal["a"][driver]
    ):

        # Test if DriverError is raised for gdal < driver_mode_mingdal
        with pytest.raises(DriverError):
            with fiona.open(path, "a", driver=driver) as c:
                c.writerecords(records2)

    else:
        # Test if we can append
        with fiona.open(path, "a", driver=driver) as c:
            c.writerecords(records2)

        if driver in {"FileGDB", "OpenFileGDB"}:
            open_driver = driver
        else:
            open_driver = None

        with fiona.open(path, driver=open_driver) as collection:
            assert collection.driver == driver
            assert len(list(collection)) == len(records1) + len(records2)


@pytest.mark.parametrize(
    "driver",
    [
        driver
        for driver in driver_mode_mingdal["a"].keys()
        if driver in supported_drivers
    ],
)
def test_append_does_not_work_when_gdal_smaller_mingdal(
    tmpdir, driver, testdata_generator, monkeypatch
):
    """Test if driver supports append mode.

    If this test fails, it should be considered to update driver_mode_mingdal in drvsupport.py.

    """

    if driver == "BNA" and GDALVersion.runtime() < GDALVersion(2, 0):
        pytest.skip("BNA driver segfaults with gdal 1.11")

    path = str(tmpdir.join(get_temp_filename(driver)))
    schema, crs, records1, records2, test_equal, create_kwargs = testdata_generator(
        driver, range(0, 5), range(5, 10)
    )

    # If driver is not able to write, we cannot test append
    if driver in driver_mode_mingdal[
        "w"
    ] and get_gdal_version_num() < calc_gdal_version_num(
        *driver_mode_mingdal["w"][driver]
    ):
        return

    # Create test file to append to
    with fiona.open(
        path, "w", driver=driver, crs=crs, schema=schema, **create_kwargs
    ) as c:

        c.writerecords(records1)

    if driver in driver_mode_mingdal[
        "a"
    ] and get_gdal_version_num() < calc_gdal_version_num(
        *driver_mode_mingdal["a"][driver]
    ):
        # Test if driver really can't append for gdal < driver_mode_mingdal

        monkeypatch.delitem(fiona.drvsupport.driver_mode_mingdal["a"], driver)

        with pytest.raises(Exception):
            with fiona.open(path, "a", driver=driver) as c:
                c.writerecords(records2)

            if driver in {"FileGDB", "OpenFileGDB"}:
                open_driver = driver
            else:
                open_driver = None

            with fiona.open(path, driver=open_driver) as collection:
                assert collection.driver == driver
                assert len(list(collection)) == len(records1) + len(records2)


@pytest.mark.parametrize(
    "driver", [driver for driver, raw in supported_drivers.items() if raw == "r"]
)
def test_no_write_driver_cannot_write(tmpdir, driver, testdata_generator, monkeypatch):
    """Test if read only driver cannot write

    If this test fails, it should be considered to enable write support for the respective driver in drvsupport.py.

    """

    monkeypatch.setitem(fiona.drvsupport.supported_drivers, driver, "rw")
    schema, crs, records1, _, test_equal, create_kwargs = testdata_generator(
        driver, range(0, 5), []
    )

    if driver == "BNA" and GDALVersion.runtime() < GDALVersion(2, 0):
        pytest.skip("BNA driver segfaults with gdal 1.11")

    if driver == "FlatGeobuf":
        pytest.xfail("FlatGeobuf doesn't raise an error but doesn't have write support")

    path = str(tmpdir.join(get_temp_filename(driver)))

    with pytest.raises(Exception):
        with fiona.open(
            path, "w", driver=driver, crs=crs, schema=schema, **create_kwargs
        ) as c:
            c.writerecords(records1)


@pytest.mark.parametrize(
    "driver",
    [
        driver
        for driver, raw in supported_drivers.items()
        if "w" in raw and "a" not in raw
    ],
)
def test_no_append_driver_cannot_append(
    tmpdir, driver, testdata_generator, monkeypatch
):
    """
    Test if a driver that supports write and not append cannot also append

    If this test fails, it should be considered to enable append support for the respective driver in drvsupport.py.

    """

    monkeypatch.setitem(fiona.drvsupport.supported_drivers, driver, "raw")

    if driver == "BNA" and GDALVersion.runtime() < GDALVersion(2, 0):
        pytest.skip("BNA driver segfaults with gdal 1.11")

    path = str(tmpdir.join(get_temp_filename(driver)))
    schema, crs, records1, records2, test_equal, create_kwargs = testdata_generator(
        driver, range(0, 5), range(5, 10)
    )

    # If driver is not able to write, we cannot test append
    if driver in driver_mode_mingdal[
        "w"
    ] and get_gdal_version_num() < calc_gdal_version_num(
        *driver_mode_mingdal["w"][driver]
    ):
        return

    # Create test file to append to
    with fiona.open(
        path, "w", driver=driver, crs=crs, schema=schema, **create_kwargs
    ) as c:

        c.writerecords(records1)

    try:
        with fiona.open(path, "a", driver=driver) as c:
            c.writerecords(records2)
    except Exception as exc:
        log.exception("Caught exception in trying to append.")
        return

    if driver in {"FileGDB", "OpenFileGDB"}:
        open_driver = driver
    else:
        open_driver = None

    with fiona.open(path, driver=open_driver) as collection:
        assert collection.driver == driver
        assert len(list(collection)) == len(records1)


def test_mingdal_drivers_are_supported():
    """Test if mode and driver is enabled in supported_drivers"""
    for mode in driver_mode_mingdal:
        for driver in driver_mode_mingdal[mode]:
            # we cannot test drivers that are not present in the gdal installation
            if driver in supported_drivers:
                assert mode in supported_drivers[driver]
