"""pytest fixtures and automatic test data generation."""

import copy
import json
import os.path
import shutil
import tarfile
import zipfile
from collections import OrderedDict
from click.testing import CliRunner
import pytest

import fiona
from fiona.crs import from_epsg
from fiona.env import GDALVersion

driver_extensions = {'DXF': 'dxf',
                     'CSV': 'csv',
                     'ESRI Shapefile': 'shp',
                     'FileGDB': 'gdb',
                     'GML': 'gml',
                     'GPX': 'gpx',
                     'GPSTrackMaker': 'gtm',
                     'MapInfo File': 'tab',
                     'DGN': 'dgn',
                     'GPKG': 'gpkg',
                     'GeoJSON': 'json',
                     'GeoJSONSeq': 'geojsons',
                     'GMT': 'gmt',
                     'OGR_GMT': 'gmt',
                     'BNA': 'bna',
                     'FlatGeobuf': 'fgb'}


def pytest_report_header(config):
    headers = []
    # gdal version number
    gdal_release_name = fiona.get_gdal_release_name()
    headers.append('GDAL: {} ({})'.format(gdal_release_name, fiona.get_gdal_version_num()))
    supported_drivers = ", ".join(sorted(list(fiona.drvsupport.supported_drivers.keys())))
    # supported drivers
    headers.append("Supported drivers: {}".format(supported_drivers))
    return '\n'.join(headers)


def get_temp_filename(driver):

    basename = "foo"
    extension = driver_extensions.get(driver, "bar")
    prefix = ""
    if driver == 'GeoJSONSeq':
        prefix = "GeoJSONSeq:"

    return "{prefix}{basename}.{extension}".format(prefix=prefix,
                                                   basename=basename,
                                                   extension=extension)


_COUTWILDRNP_FILES = [
    'coutwildrnp.shp', 'coutwildrnp.shx', 'coutwildrnp.dbf', 'coutwildrnp.prj']


def _read_file(name):
    with open(os.path.join(os.path.dirname(__file__), name)) as f:
        return f.read()


has_gpkg = "GPKG" in fiona.drvsupport.supported_drivers.keys()
has_gpkg_reason = "Requires geopackage driver"
requires_gpkg = pytest.mark.skipif(not has_gpkg, reason=has_gpkg_reason)


@pytest.fixture(scope='function')
def gdalenv(request):
    import fiona.env

    def fin():
        if fiona.env.local._env:
            fiona.env.delenv()
            fiona.env.local._env = None
    request.addfinalizer(fin)


@pytest.fixture(scope='session')
def data_dir():
    """Absolute file path to the directory containing test datasets."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))


@pytest.fixture(scope='function')
def data(tmpdir, data_dir):
    """A temporary directory containing a copy of the files in data."""
    for filename in _COUTWILDRNP_FILES:
        shutil.copy(os.path.join(data_dir, filename), str(tmpdir))
    return tmpdir


@pytest.fixture(scope='session')
def path_curves_line_csv(data_dir):
    """Path to ```curves_line.csv``"""
    return os.path.join(data_dir, 'curves_line.csv')


@pytest.fixture(scope='session')
def path_test_tin_shp(data_dir):
    """Path to ```test_tin.shp``"""
    return os.path.join(data_dir, 'test_tin.shp')

@pytest.fixture(scope='session')
def path_test_tin_csv(data_dir):
    """Path to ```test_tin.csv``"""
    return os.path.join(data_dir, 'test_tin.csv')

@pytest.fixture(scope='session')
def path_coutwildrnp_shp(data_dir):
    """Path to ```coutwildrnp.shp``"""
    return os.path.join(data_dir, 'coutwildrnp.shp')


@pytest.fixture(scope='session')
def path_coutwildrnp_zip(data_dir):
    """Creates ``coutwildrnp.zip`` if it does not exist and returns the absolute
    file path."""
    path = os.path.join(data_dir, 'coutwildrnp.zip')
    if not os.path.exists(path):
        with zipfile.ZipFile(path, 'w') as zip:
            for filename in _COUTWILDRNP_FILES:
                zip.write(os.path.join(data_dir, filename), filename)
    return path


@pytest.fixture(scope='session')
def path_grenada_geojson(data_dir):
    """Path to ```grenada.geojson```"""
    return os.path.join(data_dir, 'grenada.geojson')


@pytest.fixture(scope='session')
def bytes_coutwildrnp_zip(path_coutwildrnp_zip):
    """The zip file's bytes"""
    with open(path_coutwildrnp_zip, 'rb') as src:
        return src.read()


@pytest.fixture(scope='session')
def path_coutwildrnp_tar(data_dir):
    """Creates ``coutwildrnp.tar`` if it does not exist and returns the absolute
    file path."""
    path = os.path.join(data_dir, 'coutwildrnp.tar')
    if not os.path.exists(path):
        with tarfile.open(path, 'w') as tar:
            for filename in _COUTWILDRNP_FILES:
                tar.add(
                    os.path.join(data_dir, filename),
                    arcname=os.path.join('testing', filename))
    return path


@pytest.fixture(scope='session')
def path_coutwildrnp_json(data_dir):
    """Creates ``coutwildrnp.json`` if it does not exist and returns the absolute
    file path."""
    path = os.path.join(data_dir, 'coutwildrnp.json')
    if not os.path.exists(path):
        name = _COUTWILDRNP_FILES[0]
        with fiona.open(os.path.join(data_dir, name), 'r') as source:
            features = [feat for feat in source]
        my_layer = {
            'type': 'FeatureCollection',
            'features': features}
        with open(path, 'w') as f:
            f.write(json.dumps(my_layer))
    return path


@pytest.fixture(scope='session')
def bytes_grenada_geojson(path_grenada_geojson):
    """The geojson as bytes."""
    with open(path_grenada_geojson, 'rb') as src:
        return src.read()


@pytest.fixture(scope='session')
def path_coutwildrnp_gpkg(data_dir):
    """Creates ``coutwildrnp.gpkg`` if it does not exist and returns the absolute
    file path."""
    if not has_gpkg:
        raise RuntimeError("GDAL has not been compiled with GPKG support")
    path = os.path.join(data_dir, 'coutwildrnp.gpkg')
    if not os.path.exists(path):
        filename_shp = _COUTWILDRNP_FILES[0]
        path_shp = os.path.join(data_dir, filename_shp)
        with fiona.open(path_shp, "r") as src:
            meta = copy.deepcopy(src.meta)
            meta["driver"] = "GPKG"
            with fiona.open(path, "w", **meta) as dst:
                dst.writerecords(src)
    return path


@pytest.fixture(scope='session')
def path_gpx(data_dir):
    return os.path.join(data_dir, 'test_gpx.gpx')


@pytest.fixture(scope='session')
def feature_collection():
    """GeoJSON feature collection on a single line."""
    return _read_file(os.path.join('data', 'collection.txt'))


@pytest.fixture(scope='session')
def feature_collection_pp():
    """Same as above but with pretty-print styling applied."""
    return _read_file(os.path.join('data', 'collection-pp.txt'))


@pytest.fixture(scope='session')
def feature_seq():
    """One feature per line."""
    return _read_file(os.path.join('data', 'sequence.txt'))


@pytest.fixture(scope='session')
def feature_seq_pp_rs():
    """Same as above but each feature has pretty-print styling"""
    return _read_file(os.path.join('data', 'sequence-pp.txt'))


@pytest.fixture(scope='session')
def runner():
    """Returns a ```click.testing.CliRunner()`` instance."""
    return CliRunner()


@pytest.fixture(scope='class')
def uttc_path_coutwildrnp_zip(path_coutwildrnp_zip, request):
    """Make the ``path_coutwildrnp_zip`` fixture work with a
    ``unittest.TestCase()``.  ``uttc`` stands for unittest test case."""
    request.cls.path_coutwildrnp_zip = path_coutwildrnp_zip


@pytest.fixture(scope='class')
def uttc_path_coutwildrnp_tar(path_coutwildrnp_tar, request):
    """Make the ``path_coutwildrnp_tar`` fixture work with a
    ``unittest.TestCase()``.  ``uttc`` stands for unittest test case."""
    request.cls.path_coutwildrnp_tar = path_coutwildrnp_tar


@pytest.fixture(scope='class')
def uttc_path_coutwildrnp_json(path_coutwildrnp_json, request):
    """Make the ``path_coutwildrnp_json`` fixture work with a
    ``unittest.TestCase()``.  ``uttc`` stands for unittest test case."""
    request.cls.path_coutwildrnp_json = path_coutwildrnp_json


@pytest.fixture(scope='class')
def uttc_data_dir(data_dir, request):
    """Make the ``data_dir`` fixture work with a ``unittest.TestCase()``.
    ``uttc`` stands for unittest test case."""
    request.cls.data_dir = data_dir


@pytest.fixture(scope='class')
def uttc_path_gpx(path_gpx, request):
    """Make the ``path_gpx`` fixture work with a ``unittest.TestCase()``.
    ``uttc`` stands for unittest test case."""
    request.cls.path_gpx = path_gpx


# GDAL 2.3.x silently converts ESRI WKT to OGC WKT
# The regular expression below will match against either
WGS84PATTERN = 'GEOGCS\["(?:GCS_WGS_1984|WGS 84)",DATUM\["WGS_1984",SPHEROID\["WGS[_ ]84"'

# Define helpers to skip tests based on GDAL version
gdal_version = GDALVersion.runtime()

requires_only_gdal1 = pytest.mark.skipif(
    gdal_version.major != 1,
    reason="Only relevant for GDAL 1.x")

requires_gdal2 = pytest.mark.skipif(
    not gdal_version.major >= 2,
    reason="Requires GDAL 2.x")

requires_gdal21 = pytest.mark.skipif(
    not gdal_version.at_least('2.1'),
    reason="Requires GDAL 2.1.x")

requires_gdal22 = pytest.mark.skipif(
    not gdal_version.at_least('2.2'),
    reason="Requires GDAL 2.2.x")

requires_gdal24 = pytest.mark.skipif(
    not gdal_version.at_least('2.4'),
    reason="Requires GDAL 2.4.x")

requires_gdal_lt_3 = pytest.mark.skipif(
    not gdal_version.major < 3,
    reason="Requires GDAL < 3")

requires_gdal3 = pytest.mark.skipif(
    not gdal_version.major >= 3,
    reason="Requires GDAL 3.x")

travis_only = pytest.mark.skipif(
    not os.getenv("TRAVIS", "false") == "true",
    reason="Requires travis CI environment"
)


@pytest.fixture(scope="class")
def unittest_data_dir(data_dir, request):
    """Makes data_dir available to unittest tests"""
    request.cls.data_dir = data_dir


@pytest.fixture(scope="class")
def unittest_path_coutwildrnp_shp(path_coutwildrnp_shp, request):
    """Makes shapefile path available to unittest tests"""
    request.cls.path_coutwildrnp_shp = path_coutwildrnp_shp


@pytest.fixture()
def testdata_generator():
    """ Helper function to create test data sets for ideally all supported drivers
    """

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

    def get_crs(driver):
        special_crs = {'MapInfo File': from_epsg(4326)}
        return special_crs.get(driver, None)

    def get_records(driver, range):
        special_records1 = {'CSV': [{'geometry': None, 'properties': {'position': i}} for i in range],
                            'BNA': [{'geometry': {'type': 'Point', 'coordinates': (0.0, float(i))}, 'properties': {}}
                                    for i
                                    in range],
                            'DXF': [
                                {'geometry': {'type': 'Point', 'coordinates': (0.0, float(i))},
                                 'properties': OrderedDict(
                                     [('Layer', '0'),
                                      ('SubClasses', 'AcDbEntity:AcDbPoint'),
                                      ('Linetype', None),
                                      ('EntityHandle', str(i + 20000)),
                                      ('Text', None)])} for i in range],
                            'GPX': [{'geometry': {'type': 'Point', 'coordinates': (0.0, float(i))},
                                     'properties': {'ele': 0.0, 'time': '2020-03-24T16:08:40+00:00'}} for i
                                    in range],
                            'GPSTrackMaker': [{'geometry': {'type': 'Point', 'coordinates': (0.0, float(i))},
                                               'properties': {}} for i in range],
                            'DGN': [
                                {'geometry': {'type': 'LineString', 'coordinates': [(float(i), 0.0), (0.0, 0.0)]},
                                 'properties': {}} for i in range],
                            'MapInfo File': [
                                {'geometry': {'type': 'Point', 'coordinates': (0.0, float(i))},
                                 'properties': {'position': str(i)}} for i in range],
                            'PCIDSK': [{'geometry': {'type': 'Point', 'coordinates': (0.0, float(i), 0.0)},
                                        'properties': {'position': i}} for i in range]
                            }
        return special_records1.get(driver, [
            {'geometry': {'type': 'Point', 'coordinates': (0.0, float(i))}, 'properties': {'position': i}} for i in
            range])

    def get_records2(driver, range):
        special_records2 = {'DGN': [
            {'geometry': {'type': 'LineString', 'coordinates': [(float(i), 0.0), (0.0, 0.0)]},
             'properties': OrderedDict(
                 [('Type', 4),
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

    def get_create_kwargs(driver):
        kwargs = {
            'FlatGeobuf': {'SPATIAL_INDEX': False}
        }
        return kwargs.get(driver, {})

    def test_equal(driver, val_in, val_out):
        is_good = True
        is_good = is_good and val_in['geometry'] == val_out['geometry']
        for key in val_in['properties']:
            if key in val_out['properties']:
                if driver == 'FileGDB' and isinstance(val_in['properties'][key], int):
                    is_good = is_good and str(val_in['properties'][key]) == str(int(val_out['properties'][key]))
                else:
                    is_good = is_good and str(val_in['properties'][key]) == str(val_out['properties'][key])
            else:
                is_good = False
        return is_good

    def _testdata_generator(driver, range1, range2):
        """ Generate test data and helper methods for a specific driver. Each set of generated set of records
        contains the position specified with range. These positions are either encoded as field or in the geometry
        of the record, depending of the driver characteristics.

        Parameters
        ----------
            driver: str
                Name of drive to generate tests for
            range1: list of integer
                Range of positions for first set of records
            range2: list of integer
                Range  of positions for second set of records

        Returns
        -------
        schema
            A schema for the records
        crs
            A crs for the records
        records1
            A set of records containing the positions of range1
        records2
            A set of records containing the positions of range2
        test_equal
            A function that returns True if the geometry is equal between the generated records and a record and if
            the properties of the generated records can be found in a record
        """
        return get_schema(driver), get_crs(driver), get_records(driver, range1), get_records2(driver, range2),\
               test_equal, get_create_kwargs(driver)

    return _testdata_generator


@pytest.fixture(scope='session')
def path_test_tz_geojson(data_dir):
    """Path to ```test_tz.geojson``"""
    return os.path.join(data_dir, 'test_tz.geojson')
