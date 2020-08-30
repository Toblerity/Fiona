"""Tests of MemoryFile and ZippedMemoryFile"""
import os
import shutil
from io import BytesIO
import pytest
import fiona
from fiona.errors import FionaValueError, DriverError
from fiona.io import MemoryFile, ZipMemoryFile
from fiona.drvsupport import supported_drivers, _memoryfile_supports_mode, _memoryfile_not_supported,\
    _zip_memoryfile_supports_mode, _zip_memoryfile_not_supported, _driver_supports_mode
from fiona.env import GDALVersion
from fiona.path import ARCHIVESCHEMES
from tests.conftest import driver_extensions, get_temp_filename

gdal_version = GDALVersion.runtime()


@pytest.fixture(scope='session')
def profile_first_coutwildrnp_shp(path_coutwildrnp_shp):
    with fiona.open(path_coutwildrnp_shp) as col:
        return col.profile, next(iter(col))


@pytest.fixture(scope='session')
def data_coutwildrnp_json(path_coutwildrnp_json):
    with open(path_coutwildrnp_json, 'rb') as f:
        return f.read()


def test_memoryfile(path_coutwildrnp_json):
    """In-memory GeoJSON file can be read"""
    with open(path_coutwildrnp_json, 'rb') as f:
        data = f.read()
    with MemoryFile(data) as memfile:
        with memfile.open() as collection:
            assert len(collection) == 67


def test_zip_memoryfile(bytes_coutwildrnp_zip):
    """In-memory zipped Shapefile can be read"""
    with ZipMemoryFile(bytes_coutwildrnp_zip) as memfile:
        with memfile.open('coutwildrnp.shp') as collection:
            assert len(collection) == 67


def test_zip_memoryfile_listdir(bytes_coutwildrnp_zip):
    """In-memory /vsizip/ can list directories"""

    with ZipMemoryFile(bytes_coutwildrnp_zip) as memfile:
        assert set(memfile.listdir('/')) == {'coutwildrnp.shp', 'coutwildrnp.shx', 'coutwildrnp.dbf', 'coutwildrnp.prj'}


def test_tar_memoryfile_listdir(bytes_coutwildrnp_tar):
    """In-memory /vsitar/ can list directories"""

    with ZipMemoryFile(bytes_coutwildrnp_tar, ext='tar') as memfile:
        assert set(memfile.listdir('/testing')) == {'coutwildrnp.shp', 'coutwildrnp.shx', 'coutwildrnp.dbf',
                                                    'coutwildrnp.prj'}


def test_zip_memoryfile_listlayers(bytes_coutwildrnp_zip):
    """Test list layers of ZipMemoryFile"""

    with ZipMemoryFile(bytes_coutwildrnp_zip) as memfile:
        assert memfile.listlayers('/coutwildrnp.shp') == ['coutwildrnp']


def test_tar_memoryfile_listlayers(bytes_coutwildrnp_tar):
    """Test list layers of ZipMemoryFile"""
    with ZipMemoryFile(bytes_coutwildrnp_tar, ext='tar') as memfile:
        assert memfile.listlayers('/testing/coutwildrnp.shp') == ['coutwildrnp']


@pytest.mark.parametrize('driver', [driver for driver in supported_drivers if
                                    _driver_supports_mode(driver, 'w')])
@pytest.mark.parametrize('ext', ARCHIVESCHEMES.keys())
def test_zip_memoryfile_write_or_valueerror(ext, driver, testdata_generator):
    """ Test if it possible to write to ZipMemoryFile or FionaValueError is raised"""

    range1 = list(range(0, 5))
    range2 = list(range(5, 10))
    schema, crs, records1, records2, test_equal = testdata_generator(driver, range1, range2)

    file1_path = "/{}".format(get_temp_filename(driver))
    file2_path = "/directory/{}".format(get_temp_filename(driver))

    # \vsitar\ does not allow write mode
    if ARCHIVESCHEMES[ext] == 'tar':
        with pytest.raises(FionaValueError):
            with ZipMemoryFile(ext=ext) as memfile:
                with memfile.open(path=file1_path, mode='w', driver=driver, schema=schema) as c:
                    pass
    elif ARCHIVESCHEMES[ext] == 'zip' and not _zip_memoryfile_supports_mode('/vsizip/', driver, 'w'):
        with pytest.raises(FionaValueError):
            with ZipMemoryFile(ext=ext) as memfile:
                with memfile.open(path=file1_path, mode='w', driver=driver, schema=schema) as c:
                    pass
    else:
        with ZipMemoryFile(ext=ext) as memfile:
            with memfile.open(path=file1_path, mode='w', driver=driver, schema=schema) as c:
                c.writerecords(records1)
            with memfile.open(path=file2_path, mode='w', driver=driver, schema=schema) as c:
                c.writerecords(records2)

            with memfile.open(path=file1_path, mode='r', driver=driver, schema=schema) as c:
                assert driver == c.driver
                items = list(c)
                assert len(items) == len(range1)
                for val_in, val_out in zip(records1, items):
                    assert test_equal(driver, val_in, val_out)

            with memfile.open(path=file2_path, mode='r') as c:
                assert driver == c.driver
                items = list(c)
                assert len(items) == len(range2)
                for val_in, val_out in zip(records2, items):
                    assert test_equal(driver, val_in, val_out)


@pytest.mark.parametrize('driver', [driver for driver, mingdal in _zip_memoryfile_not_supported['/vsizip/']['w'].items()
                                    if not _zip_memoryfile_supports_mode('/vsizip/', driver, 'w')])
def test_zip_memoryfile_write_notsupported(driver, monkeypatch, testdata_generator):
    """ Test driver that are marked as having no write support for /vsizip/, can not write /vsizip/

    Note: This driver tests only the "standard case". Success of this test does not necessarily mean that driver
          does not allow to write. (e.g. requiring a special schema)

          If this test fails, it should be considered to update
          fiona.drvsupport._zip_memoryfile_not_supported['/vsizip/']['w'][driver] = GDALVersion(major, minor)
    """

    if gdal_version < GDALVersion(2, 0) and driver == 'BNA':
        pytest.skip("BNA driver segfaults with gdal 1.x")

    if gdal_version > GDALVersion(2, 2) and driver == 'DGN':
        pytest.skip("DGN driver segfaults with > gdal 2.2")

    monkeypatch.delitem(fiona.drvsupport._zip_memoryfile_not_supported['/vsizip/']['w'], driver)

    ext = 'zip'
    range1 = list(range(0, 5))
    range2 = list(range(5, 10))
    schema, crs, records1, records2, test_equal = testdata_generator(driver, range1, range2)
    file1_path = "/{}".format(get_temp_filename(driver))
    file2_path = "/directory/{}".format(get_temp_filename(driver))

    is_good = True

    try:
        with ZipMemoryFile(ext=ext) as memfile:
            with memfile.open(path=file1_path, mode='w', driver=driver, schema=schema) as c:
                c.writerecords(records1)
            with memfile.open(path=file2_path, mode='w', driver=driver, schema=schema) as c:
                c.writerecords(records2)

            with memfile.open(path=file1_path, mode='r', driver=driver, schema=schema) as c:
                assert driver == c.driver
                items = list(c)
                is_good = is_good and (len(items) == len(range1))
                for val_in, val_out in zip(records1, items):
                    is_good = is_good and test_equal(driver, val_in, val_out)

            with memfile.open(path=file2_path, mode='r') as c:
                items = list(c)
                is_good = is_good and (len(items) == len(range2))
                for val_in, val_out in zip(records2, items):
                    is_good = is_good and test_equal(driver, val_in, val_out)
    except Exception as e:
        is_good = False

    assert not is_good


@pytest.mark.parametrize('ext', ARCHIVESCHEMES.keys())
def test_zip_memoryfile_append(ext, testdata_generator):
    """ In-memory archive file cannot be appended to"""
    with pytest.raises(FionaValueError):

        range1 = list(range(0, 5))
        range2 = list(range(5, 10))
        schema, crs, records1, records2, test_equal = testdata_generator('GeoJSON', range1, range2)

        with ZipMemoryFile(ext=ext) as memfile:
            with memfile.open(path="/test1.geojson", mode='w', driver='GeoJSON', schema=schema) as c:
                c.writerecords(records1)

            with memfile.open(path="/test1.geojson", mode='a', driver='GeoJSON', schema=schema) as c:
                c.writerecords(records2)

            with memfile.open(path="/test1.geojson", mode='r', driver='GeoJSON', schema=schema) as c:
                items = list(c)
                assert len(items) == len(range(0, 10))
                for val_in, val_out in zip(records1 + records2, items):
                    assert test_equal('GeoJSON', val_in, val_out)


@pytest.mark.parametrize('driver', [driver for driver in supported_drivers if
                                    _driver_supports_mode(driver, 'w')])
def test_write_memoryfile_or_driver_error(driver, testdata_generator):
    """ Test if driver can write to MemoryFile or raises DriverError if not supported """

    range1 = list(range(0, 5))
    schema, crs, records1, _, test_equal = testdata_generator(driver, range1, [])

    if not _memoryfile_supports_mode(driver, 'w'):
        with pytest.raises(DriverError):
            with MemoryFile(ext=driver_extensions.get(driver, '')) as memfile:
                with memfile.open(driver=driver, schema=schema) as c:
                    c.writerecords(records1)

                with memfile.open(driver=driver) as c:
                    items = list(c)
                    assert len(items) == len(range1)
                    for val_in, val_out in zip(records1, items):
                        assert test_equal(driver, val_in, val_out)
    else:
        # BNA requires extension: fiona.errors.DriverError: '/vsimem/...' not recognized as a supported file format.
        with MemoryFile(ext=driver_extensions.get(driver, '')) as memfile:
            with memfile.open(driver=driver, schema=schema) as c:
                c.writerecords(records1)

            with memfile.open(driver=driver) as c:
                assert driver == c.driver
                items = list(c)
                assert len(items) == len(range1)
                for val_in, val_out in zip(records1, items):
                    assert test_equal(driver, val_in, val_out)


@pytest.mark.parametrize('driver', [driver for driver, mingdal in _memoryfile_not_supported['w'].items() if
                                    not _memoryfile_supports_mode(driver, 'w')])
def test_write_memoryfile_notsupported(driver, monkeypatch, testdata_generator):
    """ Test if drivers marked to not be able to write to MemoryFile, can not write to MemoryFile

    Note: This driver tests only the "standard case". Success of this test does not necessarily mean that driver
          does not allow to write. (e.g. requiring a special schema)

          If this test fails, it should be considered to update
          fiona.drvsupport._memoryfile_not_supported['w'][driver] = GDALVersion(major, minor)
    """

    if gdal_version < GDALVersion(2, 0) and driver == 'BNA':
        pytest.skip("BNA driver segfaults with gdal 1.x")

    if gdal_version > GDALVersion(2, 2) and driver == 'DGN':
        pytest.skip("DGN driver segfaults with > gdal 2.2")

    monkeypatch.delitem(fiona.drvsupport._memoryfile_not_supported['w'], driver)

    range1 = list(range(0, 5))
    schema, crs, records1, _, test_equal = testdata_generator('GeoJSON', range1, [])

    is_good = True

    try:
        with MemoryFile() as memfile:
            with memfile.open(driver=driver, schema=schema) as c:
                c.writerecords(records1)

            with memfile.open(driver=driver) as c:
                items = list(c)
                is_good = is_good and (len(items) == len(records1))
                for val_in, val_out in zip(records1, items):
                    is_good = is_good and test_equal(driver, val_in, val_out)
    except Exception as e:
        is_good = False

    assert not is_good


@pytest.mark.parametrize('driver', [driver for driver in supported_drivers if _driver_supports_mode(driver, 'a')])
def test_append_memoryfile_or_drivererror(driver, testdata_generator):
    """ Test if driver can append to MemoryFile or raises DriverError if not supported  """

    range1 = list(range(0, 5))
    range2 = list(range(5, 10))
    schema, crs, records1, records2, test_equal = testdata_generator(driver, range1, range2)
    positions = range1 + range2

    if not _memoryfile_supports_mode(driver, 'a'):
        with pytest.raises(FionaValueError):
            with MemoryFile(ext=driver_extensions.get(driver, '')) as memfile:
                with memfile.open(driver=driver, schema=schema) as c:
                    c.writerecords(records1)
                with memfile.open(driver=driver, schema=schema, mode='a') as c:
                    c.writerecords(records2)
    else:
        # GPKG driver for gdal 2.0 needs extensions, otherwise SQLite driver is used
        with MemoryFile(ext=driver_extensions.get(driver, '')) as memfile:
            with memfile.open(driver=driver, schema=schema) as c:
                c.writerecords(records1)
            with memfile.open(driver=driver, schema=schema, mode='a') as c:
                c.writerecords(records2)
            with memfile.open(driver=driver) as c:
                items = list(c)
                assert len(items) == len(positions)
                for val_in, val_out in zip(records1 + records2, items):
                    assert test_equal(driver, val_in, val_out)


@pytest.mark.parametrize('driver', [driver for driver, mingdal in _memoryfile_not_supported['a'].items() if
                                    not _memoryfile_supports_mode(driver, 'a')])
def test_append_memoryfile_notsupported(driver, monkeypatch, testdata_generator):
    """ Test if drivers marked to not be able to append to MemoryFile, can not append to MemoryFile

    Note: This driver tests only the "standard case". Success of this test does not necessarily mean that driver
          does not allow to appended. (e.g. requiring a special schema)

          If this test fails, it should be considered to update
          fiona.drvsupport._memoryfile_not_supported['a'][driver] = GDALVersion(major, minor)
    """

    if gdal_version < GDALVersion(2, 0) and driver == 'BNA':
        pytest.skip("BNA driver segfaults with gdal 1.x")

    if gdal_version > GDALVersion(2, 2) and driver == 'DGN':
        pytest.skip("DGN driver segfaults with > gdal 2.2")

    monkeypatch.delitem(fiona.drvsupport._memoryfile_not_supported['a'], driver)

    range1 = list(range(0, 5))
    range2 = list(range(5, 10))
    schema, crs, records1, records2, test_equal = testdata_generator(driver, range1, range2)
    positions = range1 + range2

    is_good = True

    try:
        with MemoryFile() as memfile:
            with memfile.open(driver=driver, schema=schema) as c:
                c.writerecords(records1)
            with memfile.open(driver=driver, schema=schema, mode='a') as c:
                c.writerecords(records2)
            with memfile.open(driver=driver) as c:
                items = list(c)

                is_good = is_good and (len(items) == len(positions))
                for val_in, val_out in zip(records1 + records2, items):
                    is_good = is_good and test_equal(driver, val_in, val_out)
    except:
        is_good = False

    assert not is_good


def test_memoryfile_bytesio(data_coutwildrnp_json):
    """GeoJSON file stored in BytesIO can be read"""
    with fiona.open(BytesIO(data_coutwildrnp_json)) as collection:
        assert len(collection) == 67


def test_memoryfile_fileobj(path_coutwildrnp_json):
    """In-memory GeoJSON file can be read"""
    with open(path_coutwildrnp_json, 'rb') as f:
        with fiona.open(f) as collection:
            assert len(collection) == 67


def test_memoryfilebase_write():
    """Test MemoryFileBase.write """

    schema = {'geometry': 'Point', 'properties': [('position', 'int')]}
    records = [{'geometry': {'type': 'Point', 'coordinates': (0.0, float(i))}, 'properties': {'position': i}} for i in
               range(5)]

    with MemoryFile() as memfile:
        with BytesIO() as fout:
            with fiona.open(fout,
                            'w',
                            driver="GeoJSON",
                            schema=schema) as c:
                c.writerecords(records)
            fout.seek(0)
            data = fout.read()

        assert memfile.tell() == 0
        memfile.write(data)

        with memfile.open(driver="GeoJSON",
                          schema=schema) as c:
            record_positions = [int(f['properties']['position']) for f in c]
            assert record_positions == list(range(5))


@pytest.mark.parametrize('driver', [driver for driver in supported_drivers if
                                    _driver_supports_mode(driver, 'w') and _memoryfile_supports_mode(driver, 'w')])
def test_memoryfile_exists_no_extension(driver, testdata_generator):
    """ Test MemoryFileBase.exists() finds dataset when file extension is not specified """
    # TODO
    if driver in {'OGR_GMT', 'GMT'}:
        pytest.skip("GMT driver adds .gmt extension, thus the VIS path is not correct")

    range1 = list(range(0, 5))
    schema, crs, records1, records2, test_equal = testdata_generator(driver, range1, [])

    with MemoryFile() as memfile:
        with memfile.open(driver=driver, schema=schema) as c:
            c.writerecords(records1)
        assert memfile.exists()


@pytest.mark.parametrize('driver', [driver for driver in supported_drivers if
                                    _driver_supports_mode(driver, 'w') and _memoryfile_supports_mode(driver, 'w')])
def test_memoryfile_exists_with_extension(driver, testdata_generator):
    """ Test MemoryFileBase.exists() finds dataset when file extension is specified """

    range1 = list(range(0, 5))
    schema, crs, records1, records2, test_equal = testdata_generator(driver, range1, [])
    with MemoryFile(ext=driver_extensions.get(driver, '')) as memfile:
        with memfile.open(driver=driver, schema=schema) as c:
            c.writerecords(records1)
        assert memfile.exists()


def test_memoryfile_len(data_coutwildrnp_json):
    """ Test MemoryFileBase.__len__"""

    with MemoryFile() as memfile:
        assert len(memfile) == 0
        memfile.write(data_coutwildrnp_json)
        assert len(memfile) == len(data_coutwildrnp_json)


@pytest.mark.parametrize('driver', [driver for driver in supported_drivers if
                                    _driver_supports_mode(driver, 'w') and 
                                    _memoryfile_supports_mode(driver, 'w')])
def test_zipmemoryfile_write(tmpdir, driver, testdata_generator):
    """ Test if it possible to write to ZipMemoryFile or FionaValueError is raised"""

    filename = get_temp_filename(driver)
    path = str(tmpdir.mkdir("data").join(filename))
    schema, crs, records1, _, test_equal = testdata_generator(driver, range(0, 5), [])

    # Create dataset
    with fiona.open(path, 'w',
                    driver=driver,
                    crs=crs,
                    schema=schema) as c:
        c.writerecords(records1)

    # Create zip dataset
    zip_path = str(tmpdir.mkdir("zip").join("data"))
    data_path = str(tmpdir.join("data"))
    shutil.make_archive(zip_path, 'zip', data_path)
    with open(zip_path + ".zip", 'rb') as f:
        data = f.read()

    with ZipMemoryFile(file_or_bytes=data) as memfile:
        assert len(memfile) == len(data)

        with memfile.open(filename) as c:
            items = list(c)
            assert len(items) == len(records1)
            for val_in, val_out in zip(records1, items):
                assert test_equal(driver, val_in, val_out)
