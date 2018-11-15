"""pytest fixtures and automatic test data generation."""

import copy
import json
import os.path
import shutil
import tarfile
import zipfile

from click.testing import CliRunner
import pytest

import fiona
from fiona.env import GDALVersion


def pytest_report_header(config):
    headers = []
    # gdal version number
    gdal_release_name = fiona.get_gdal_release_name()
    headers.append('GDAL: {} ({})'.format(gdal_release_name, fiona.get_gdal_version_num()))
    supported_drivers = ", ".join(sorted(list(fiona.drvsupport.supported_drivers.keys())))
    # supported drivers
    headers.append("Supported drivers: {}".format(supported_drivers))
    return '\n'.join(headers)


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


@pytest.fixture(scope="class")
def unittest_data_dir(data_dir, request):
    """Makes data_dir available to unittest tests"""
    request.cls.data_dir = data_dir


@pytest.fixture(scope="class")
def unittest_path_coutwildrnp_shp(path_coutwildrnp_shp, request):
    """Makes shapefile path available to unittest tests"""
    request.cls.path_coutwildrnp_shp = path_coutwildrnp_shp
