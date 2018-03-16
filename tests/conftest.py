"""pytest fixtures and automatic test data generation."""
import json
import os.path
import tarfile
import zipfile
import copy

from click.testing import CliRunner
import pytest

import fiona

def pytest_report_header(config):
    headers = []
    # gdal version number
    gdal_release_name = fiona.get_gdal_release_name().decode("utf-8")
    headers.append('GDAL: {}'.format(gdal_release_name))
    supported_drivers = ", ".join(sorted(list(fiona.supported_drivers.keys())))
    # supported drivers
    headers.append("Supported drivers: {}".format(supported_drivers))
    return '\n'.join(headers)


_COUTWILDRNP_FILES = [
    'coutwildrnp.shp', 'coutwildrnp.shx', 'coutwildrnp.dbf', 'coutwildrnp.prj']


def _read_file(name):
    with open(os.path.join(os.path.dirname(__file__), name)) as f:
        return f.read()


has_gpkg = "GPKG" in fiona.supported_drivers.keys()
has_gpkg_reason = "Requires geopackage driver"
requires_gpkg = pytest.mark.skipif(not has_gpkg, reason=has_gpkg_reason)


@pytest.fixture(scope='session')
def data_dir():
    """Absolute file path to the directory containing test datasets."""
    return os.path.abspath(os.path.join('tests','data'))


@pytest.fixture(scope='session')
def path_coutwildrnp_shp():
    """Path to ```coutwildrnp.shp``"""
    return os.path.join(data_dir(), 'coutwildrnp.shp')


@pytest.fixture(scope='session')
def path_coutwildrnp_zip():
    """Creates ``coutwildrnp.zip`` if it does not exist and returns the absolute
    file path."""
    path = os.path.join(data_dir(), 'coutwildrnp.zip')
    if not os.path.exists(path):
        with zipfile.ZipFile(path, 'w') as zip:
            for filename in _COUTWILDRNP_FILES:
                zip.write(os.path.join(data_dir(), filename), filename)
    return path

@pytest.fixture(scope='session')
def path_grenada_geojson():
    """Path to ```grenada.geojson```"""
    return os.path.join(data_dir(), 'grenada.geojson')


@pytest.fixture(scope='session')
def bytes_coutwildrnp_zip(path_coutwildrnp_zip):
    """The zip file's bytes"""
    with open(path_coutwildrnp_zip, 'rb') as src:
        return src.read()


@pytest.fixture(scope='session')
def path_coutwildrnp_tar():
    """Creates ``coutwildrnp.tar`` if it does not exist and returns the absolute
    file path."""
    path = os.path.join(data_dir(), 'coutwildrnp.tar')
    if not os.path.exists(path):
        with tarfile.open(path, 'w') as tar:
            for filename in _COUTWILDRNP_FILES:
                tar.add(
                    os.path.join(data_dir(), filename),
                    arcname=os.path.join('testing', filename))
    return path


@pytest.fixture(scope='session')
def path_coutwildrnp_json():
    """Creates ``coutwildrnp.json`` if it does not exist and returns the absolute
    file path."""
    path = os.path.join(data_dir(), 'coutwildrnp.json')
    if not os.path.exists(path):
        name = _COUTWILDRNP_FILES[0]
        with fiona.open(os.path.join(data_dir(), name), 'r') as source:
            features = [feat for feat in source]
        my_layer = {
            'type': 'FeatureCollection',
            'features': features}
        with open(path, 'w') as f:
            f.write(json.dumps(my_layer))
    return path

@pytest.fixture(scope='session')
def bytes_grenada_geojson():
    """The geojson as bytes."""
    with open(path_grenada_geojson(), 'rb') as src:
        return src.read()


@pytest.fixture(scope='session')
def path_coutwildrnp_gpkg():
    """Creates ``coutwildrnp.gpkg`` if it does not exist and returns the absolute
    file path."""
    if not has_gpkg:
        raise RuntimeError("GDAL has not been compiled with GPKG support")
    path = os.path.join(data_dir(), 'coutwildrnp.gpkg')
    if not os.path.exists(path):
        filename_shp = _COUTWILDRNP_FILES[0]
        path_shp = os.path.join(data_dir(), filename_shp)
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
    return _read_file(os.path.join('data','collection-pp.txt'))


@pytest.fixture(scope='session')
def feature_seq():
    """One feature per line."""
    return _read_file(os.path.join('data','sequence.txt'))


@pytest.fixture(scope='session')
def feature_seq_pp_rs():
    """Same as above but each feature has pretty-print styling"""
    return _read_file(os.path.join('data','sequence-pp.txt'))


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

"""
GDAL 2.3.x silently converts ESRI WKT to OGC WKT
The regular expression below will match against either
"""
WGS84PATTERN = 'GEOGCS\["(?:GCS_WGS_1984|WGS 84)",DATUM\["WGS_1984",SPHEROID\["WGS[_ ]84"'
