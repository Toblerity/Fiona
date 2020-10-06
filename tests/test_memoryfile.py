"""Tests of MemoryFile and ZippedMemoryFile"""

from collections import OrderedDict
from io import BytesIO
import pytest
import fiona
from fiona import supported_drivers
from fiona.drvsupport import _driver_supports_mode
from fiona.errors import DriverError
from fiona.io import MemoryFile, ZipMemoryFile
from fiona.meta import supports_vsi

from .conftest import requires_gdal2


@pytest.fixture(scope='session')
def profile_first_coutwildrnp_shp(path_coutwildrnp_shp):
    with fiona.open(path_coutwildrnp_shp) as col:
        return col.profile, next(iter(col))


@pytest.fixture(scope='session')
def data_coutwildrnp_json(path_coutwildrnp_json):
    with open(path_coutwildrnp_json, 'rb') as f:
        return f.read()


def test_memoryfile_ext():
    """File extensions are handled"""
    assert MemoryFile(ext=".geojson").name.endswith(".geojson")


def test_memoryfile_bare_ext():
    """File extensions without a leading . are handled"""
    assert MemoryFile(ext="geojson").name.endswith(".geojson")


def test_memoryfile_init(data_coutwildrnp_json):
    """In-memory GeoJSON file can be read"""
    with MemoryFile(data_coutwildrnp_json) as memfile:
        with memfile.open() as collection:
            assert len(collection) == 67


def test_memoryfile_incr_init(data_coutwildrnp_json):
    """In-memory GeoJSON file written in 2 parts can be read"""
    with MemoryFile() as memfile:
        memfile.write(data_coutwildrnp_json[:1000])
        memfile.write(data_coutwildrnp_json[1000:])
        with memfile.open() as collection:
            assert len(collection) == 67


def test_zip_memoryfile(bytes_coutwildrnp_zip):
    """In-memory zipped Shapefile can be read"""
    with ZipMemoryFile(bytes_coutwildrnp_zip) as memfile:
        with memfile.open('coutwildrnp.shp') as collection:
            assert len(collection) == 67


def test_zip_memoryfile_infer_layer_name(bytes_coutwildrnp_zip):
    """In-memory zipped Shapefile can be read with the default layer"""
    with ZipMemoryFile(bytes_coutwildrnp_zip) as memfile:
        with memfile.open() as collection:
            assert len(collection) == 67


def test_open_closed():
    """Get an exception when opening a dataset on a closed MemoryFile"""
    memfile = MemoryFile()
    memfile.close()
    assert memfile.closed
    with pytest.raises(IOError):
        memfile.open()


def test_open_closed_zip():
    """Get an exception when opening a dataset on a closed ZipMemoryFile"""
    memfile = ZipMemoryFile()
    memfile.close()
    assert memfile.closed
    with pytest.raises(IOError):
        memfile.open()


def test_write_memoryfile(profile_first_coutwildrnp_shp):
    """In-memory GeoJSON can be written"""
    profile, first = profile_first_coutwildrnp_shp
    profile['driver'] = 'GeoJSON'
    with MemoryFile() as memfile:
        with memfile.open(**profile) as col:
            col.write(first)
        memfile.seek(0)
        data = memfile.read()

    with MemoryFile(data) as memfile:
        with memfile.open() as col:
            assert len(col) == 1


@requires_gdal2
def test_memoryfile_write_extension(profile_first_coutwildrnp_shp):
    """In-memory shapefile gets an .shp extension by default"""
    profile, first = profile_first_coutwildrnp_shp
    profile['driver'] = 'ESRI Shapefile'
    with MemoryFile() as memfile:
        with memfile.open(**profile) as col:
            col.write(first)
        assert memfile.name.endswith(".shp")


def test_memoryfile_open_file_or_bytes_read(path_coutwildrnp_json):
    """Test MemoryFile.open when file_or_bytes has a read attribute """
    with open(path_coutwildrnp_json, 'rb') as f:
        with MemoryFile(f) as memfile:
            with memfile.open() as collection:
                assert len(collection) == 67


def test_memoryfile_bytesio(data_coutwildrnp_json):
    """GeoJSON file stored in BytesIO can be read"""
    with fiona.open(BytesIO(data_coutwildrnp_json)) as collection:
        assert len(collection) == 67


def test_memoryfile_fileobj(path_coutwildrnp_json):
    """GeoJSON file in an open file object can be read"""
    with open(path_coutwildrnp_json, 'rb') as f:
        with fiona.open(f) as collection:
            assert len(collection) == 67


def test_memoryfile_len(data_coutwildrnp_json):
    """Test MemoryFile.__len__ """
    with MemoryFile() as memfile:
        assert len(memfile) == 0
        memfile.write(data_coutwildrnp_json)
        assert len(memfile) == len(data_coutwildrnp_json)


def test_memoryfile_tell(data_coutwildrnp_json):
    """Test MemoryFile.tell() """
    with MemoryFile() as memfile:
        assert memfile.tell() == 0
        memfile.write(data_coutwildrnp_json)
        assert memfile.tell() == len(data_coutwildrnp_json)


def test_write_bytesio(profile_first_coutwildrnp_shp):
    """GeoJSON can be written to BytesIO"""
    profile, first = profile_first_coutwildrnp_shp
    profile['driver'] = 'GeoJSON'
    with BytesIO() as fout:
        with fiona.open(fout, 'w', **profile) as col:
            col.write(first)
        fout.seek(0)
        data = fout.read()

    with MemoryFile(data) as memfile:
        with memfile.open() as col:
            assert len(col) == 1


def test_mapinfo_raises():
    """Reported to be a crasher in #937"""
    driver = 'MapInfo File'
    schema = {'geometry': 'Point', 'properties': OrderedDict([('position', 'str')])}

    with BytesIO() as fout:
        with pytest.raises(OSError):
            with fiona.open(fout, "w", driver=driver, schema=schema) as collection:
                collection.write({"type": "Feature", "geometry": {"type": "Point", "coordinates": (0, 0)}, "properties": {"position": "x"}})


# TODO remove exclusion of MapInfo File once testdata_generator is fixed
@pytest.mark.parametrize('driver', [driver for driver in supported_drivers if _driver_supports_mode(driver, 'a') and
                                    supports_vsi(driver) and driver not in {'MapInfo File'}])
def test_write_memoryfile_drivers(driver, testdata_generator):
    """ Test if driver is able to write to memoryfile """

    range1 = list(range(0, 5))
    schema, crs, records1, _, test_equal = testdata_generator(driver, range1, [])

    with MemoryFile() as memfile:
        with memfile.open(driver=driver, schema=schema) as c:
            c.writerecords(records1)

        with memfile.open(driver=driver) as c:
            assert driver == c.driver
            items = list(c)
            assert len(items) == len(range1)
            for val_in, val_out in zip(records1, items):
                assert test_equal(driver, val_in, val_out)


# TODO remove exclusion of MapInfo File once testdata_generator is fixed
@pytest.mark.parametrize('driver', [driver for driver in supported_drivers if _driver_supports_mode(driver, 'a') and
                                    supports_vsi(driver) and driver not in {'MapInfo File'}])
def test_append_memoryfile_drivers(driver, testdata_generator):
    """ Test if driver is able to append to memoryfile """
    range1 = list(range(0, 5))
    range2 = list(range(5, 10))
    schema, crs, records1, records2, test_equal = testdata_generator(driver, range1, range2)

    with MemoryFile() as memfile:
        with memfile.open(driver=driver, schema=schema) as c:
            c.writerecords(records1)

        with memfile.open(mode='a', driver=driver, schema=schema) as c:
            c.writerecords(records2)

        with memfile.open(driver=driver) as c:
            assert driver == c.driver
            items = list(c)
            assert len(items) == len(range1 + range2)
            for val_in, val_out in zip(records1 + records2, items):
                assert test_equal(driver, val_in, val_out)


def test_memoryfile_driver_does_not_support_vsi():
    """ Test that Exception is raised when a dataset is opened with a driver that does not support VSI"""
    if "FileGDB" not in supported_drivers:
        pytest.skip("FileGDB driver not available")
    with pytest.raises(DriverError):
        with MemoryFile() as memfile:
            with memfile.open(driver="FileGDB") as c:
                pass

@pytest.mark.parametrize('mode', ['r', 'a'])
def test_modes_on_non_existing_memoryfile(mode):
    """ Test that non existing memoryfile cannot opened in r or a mode"""
    with MemoryFile() as memfile:
        with pytest.raises(IOError):
            with memfile.open(mode=mode) as c:
                pass
