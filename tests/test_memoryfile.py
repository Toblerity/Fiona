"""Tests of MemoryFile and ZippedMemoryFile"""
from collections import OrderedDict
from io import BytesIO
import pytest
import fiona
from fiona.errors import FionaValueError, DriverError
from fiona.io import MemoryFile, ZipMemoryFile
from fiona.drvsupport import supported_drivers, driver_mode_mingdal, _memoryfile_supports_mode,\
    _memoryfile_not_supported, _zip_memoryfile_supports_mode, _zip_memoryfile_not_supported, _driver_supports_mode
from fiona.env import GDALVersion
from fiona.path import ARCHIVESCHEMES
from tests.conftest import driver_extensions, get_temp_filename


gdal_version = GDALVersion.runtime()


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
def test_zip_memoryfile_write(ext, driver):
    """In-memory zipped Shapefile can be written to"""

    schema = get_schema(driver)
    range1 = list(range(0, 5))
    range2 = list(range(5, 10))
    records1 = get_records(driver, range1)
    records2 = get_records(driver, range2)
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
                for val_in, val_out in zip(range1, items):
                    assert val_in == int(get_pos(val_out, driver))

            with memfile.open(path=file2_path, mode='r') as c:
                assert driver == c.driver
                items = list(c)
                assert len(items) == len(range2)
                for val_in, val_out in zip(range2, items):
                    assert val_in == int(get_pos(val_out, driver))


@pytest.mark.parametrize('driver', [driver for driver, mingdal in _zip_memoryfile_not_supported['/vsizip/']['w'].items()
                                    if not _zip_memoryfile_supports_mode('/vsizip/', driver, 'w')])
def test_zip_memoryfile_write_notsupported(driver, monkeypatch):
    """In-memory zipped Shapefile, driver that are marked as not supporting write, can not write

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
    schema = get_schema(driver)
    range1 = list(range(0, 5))
    range2 = list(range(5, 10))
    records1 = get_records(driver, range1)
    records2 = get_records(driver, range2)
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
                for val_in, val_out in zip(range1, items):
                    is_good = is_good and val_in == int(get_pos(val_out, driver))

            with memfile.open(path=file2_path, mode='r') as c:
                items = list(c)
                is_good = is_good and (len(items) == len(range2))
                for val_in, val_out in zip(range2, items):
                    is_good = is_good and val_in == int(get_pos(val_out, driver))
    except Exception as e:
        is_good = False

    assert not is_good


@pytest.mark.parametrize('ext', ARCHIVESCHEMES.keys())
def test_zip_memoryfile_append(ext):
    """ In-memory zip file cannot be appended to"""
    with pytest.raises(FionaValueError):
        schema = {'geometry': 'Point', 'properties': OrderedDict([('position', 'int')])}
        records1 = [{'geometry': {'type': 'Point', 'coordinates': (0.0, float(i))}, 'properties': {'position': i}} for i
                    in
                    range(0, 5)]
        records2 = [{'geometry': {'type': 'Point', 'coordinates': (0.0, float(i))}, 'properties': {'position': i}} for i
                    in
                    range(5, 10)]
        with ZipMemoryFile(ext=ext) as memfile:
            with memfile.open(path="/test1.geojson", mode='w', driver='GeoJSON', schema=schema) as c:
                c.writerecords(records1)

            with memfile.open(path="/test1.geojson", mode='a', driver='GeoJSON', schema=schema) as c:
                c.writerecords(records2)

            with memfile.open(path="/test1.geojson", mode='r', driver='GeoJSON', schema=schema) as c:
                items = list(c)
                assert len(items) == len(range(0, 10))
                for val_in, val_out in zip(range(0, 10), items):
                    assert val_in == int(val_out['properties']['position'])


@pytest.mark.parametrize('driver', [driver for driver in supported_drivers if
                                    _driver_supports_mode(driver, 'w')])
def test_write_memoryfile(driver):
    """In-memory can be written"""

    schema = get_schema(driver)
    positions = list(range(0, 5))
    records1 = get_records(driver, positions)

    if not _memoryfile_supports_mode(driver, 'w'):
        with pytest.raises(DriverError):
            with MemoryFile(ext=driver_extensions.get(driver, '')) as memfile:
                with memfile.open(driver=driver, schema=schema) as c:
                    c.writerecords(records1)

                with memfile.open(driver=driver) as c:
                    items = list(c)
                    assert len(items) == len(positions)
                    for val_in, val_out in zip(positions, items):
                        assert val_in == int(get_pos(val_out, driver))
    else:
        # BNA requires extension: fiona.errors.DriverError: '/vsimem/...' not recognized as a supported file format.
        with MemoryFile(ext=driver_extensions.get(driver, '')) as memfile:
            with memfile.open(driver=driver, schema=schema) as c:
                c.writerecords(records1)

            with memfile.open(driver=driver) as c:
                assert driver == c.driver
                items = list(c)
                assert len(items) == len(positions)
                for val_in, val_out in zip(positions, items):
                    assert val_in == int(get_pos(val_out, driver))


@pytest.mark.parametrize('driver', [driver for driver, mingdal in _memoryfile_not_supported['w'].items() if
                                    not _memoryfile_supports_mode(driver, 'w')])
def test_write_memoryfile_notsupported(driver, monkeypatch):
    """In-memory, driver that are marked as not supporting write, can not write

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

    schema = get_schema(driver)
    positions = list(range(0, 5))
    records1 = get_records(driver, positions)

    is_good = True

    try:
        with MemoryFile() as memfile:
            with memfile.open(driver=driver, schema=schema) as c:
                c.writerecords(records1)

            with memfile.open(driver=driver) as c:
                items = list(c)
                is_good = is_good and (len(items) == len(positions))
                for val_in, val_out in zip(positions, items):
                    is_good = is_good and (val_in == int(get_pos(val_out, driver)))
    except Exception as e:
        is_good = False

    assert not is_good


@pytest.mark.parametrize('driver', [driver for driver in supported_drivers if _driver_supports_mode(driver, 'a')])
def test_append_memoryfile(driver):
    """In-memory can be appended"""

    schema = get_schema(driver)
    range1 = list(range(0, 5))
    range2 = list(range(5, 10))
    records1 = get_records(driver, range1)
    records2 = get_records2(driver, range2)
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
                for val_in, val_out in zip(positions, items):
                    assert val_in == int(get_pos(val_out, driver))


@pytest.mark.parametrize('driver', [driver for driver, mingdal in _memoryfile_not_supported['a'].items() if
                                    not _memoryfile_supports_mode(driver, 'a')])
def test_append_memoryfile_notsupported(driver, monkeypatch):
    """In-memory, driver that are marked as not supporting appended, can not appended

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

    schema = get_schema(driver)
    range1 = list(range(0, 5))
    range2 = list(range(5, 10))
    records1 = get_records(driver, range1)
    records2 = get_records2(driver, range2)
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
                for val_in, val_out in zip(positions, items):
                    is_good = is_good and (val_in == int(get_pos(val_out, driver)))
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
def test_memoryfile_exists_no_extension(driver):

    # TODO
    if driver == 'OGR_GMT':
        pytest.skip("Driver adds .gmt extension, thus the VIS path is not correct")

    schema = get_schema(driver)
    positions = list(range(0, 5))
    records1 = get_records(driver, positions)

    with MemoryFile() as memfile:
        with memfile.open(driver=driver, schema=schema) as c:
            c.writerecords(records1)
        assert memfile.exists()


@pytest.mark.parametrize('driver', [driver for driver in supported_drivers if
                                    _driver_supports_mode(driver, 'w') and _memoryfile_supports_mode(driver, 'w')])
def test_memoryfile_exists_with_extension(driver):
    schema = get_schema(driver)
    positions = list(range(0, 5))
    records1 = get_records(driver, positions)

    with MemoryFile(ext=driver_extensions.get(driver, '')) as memfile:
        with memfile.open(driver=driver, schema=schema) as c:
            c.writerecords(records1)
        assert memfile.exists()

