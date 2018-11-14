import os
import tempfile

import pytest

import fiona
from fiona.errors import SchemaError, UnsupportedGeometryTypeError
from fiona.schema import FIELD_TYPES, normalize_field_type
from fiona.env import calc_gdal_version_num, get_gdal_version_num


def test_schema_ordering_items(tmpdir):
    name = str(tmpdir.join('test_scheme.shp'))
    items = [('title', 'str:80'), ('date', 'date')]
    with fiona.open(name, 'w',
                    driver="ESRI Shapefile",
                    schema={
                        'geometry': 'LineString',
                        'properties': items}) as c:
        assert list(c.schema['properties'].items()) == items
    with fiona.open(name) as c:
        assert list(c.schema['properties'].items()) == items


def test_shapefile_schema(tmpdir):
    name = str(tmpdir.join('test_schema.shp'))
    items = sorted({
        'AWATER10': 'float',
        'CLASSFP10': 'str',
        'ZipCodeType': 'str',
        'EstimatedPopulation': 'float',
        'LocationType': 'str',
        'ALAND10': 'float',
        'TotalWages': 'float',
        'FUNCSTAT10': 'str',
        'Long': 'float',
        'City': 'str',
        'TaxReturnsFiled': 'float',
        'State': 'str',
        'Location': 'str',
        'GSrchCnt': 'float',
        'INTPTLAT10': 'str',
        'Lat': 'float',
        'MTFCC10': 'str',
        'Decommisioned': 'str',
        'GEOID10': 'str',
        'INTPTLON10': 'str'}.items())
    with fiona.open(name, 'w',
                    driver="ESRI Shapefile",
                    schema={'geometry': 'Polygon', 'properties': items}) as c:
        assert list(c.schema['properties'].items()) == items
        c.write(
            {'geometry': {'coordinates': [[(-117.882442, 33.783633),
                                           (-117.882284, 33.783817),
                                           (-117.863348, 33.760016),
                                           (-117.863478, 33.760016),
                                           (-117.863869, 33.760017),
                                           (-117.864, 33.760017999999995),
                                           (-117.864239, 33.760019),
                                           (-117.876608, 33.755769),
                                           (-117.882886, 33.783114),
                                           (-117.882688, 33.783345),
                                           (-117.882639, 33.783401999999995),
                                           (-117.88259, 33.78346),
                                           (-117.882442, 33.783633)]],
                          'type': 'Polygon'},
             'id': '1',
             'properties': {
                'ALAND10': 8819240.0,
                'AWATER10': 309767.0,
                'CLASSFP10': 'B5',
                'City': 'SANTA ANA',
                'Decommisioned': False,
                'EstimatedPopulation': 27773.0,
                'FUNCSTAT10': 'S',
                'GEOID10': '92706',
                'GSrchCnt': 0.0,
                'INTPTLAT10': '+33.7653010',
                'INTPTLON10': '-117.8819759',
                'Lat': 33.759999999999998,
                'Location': 'NA-US-CA-SANTA ANA',
                'LocationType': 'PRIMARY',
                'Long': -117.88,
                'MTFCC10': 'G6350',
                'State': 'CA',
                'TaxReturnsFiled': 14635.0,
                'TotalWages': 521280485.0,
                'ZipCodeType': 'STANDARD'},
             'type': 'Feature'})
        assert len(c) == 1
    with fiona.open(name) as c:
        assert (
            list(c.schema['properties'].items()) ==
            sorted([('AWATER10', 'float:24.15'),
                    ('CLASSFP10', 'str:80'),
                    ('ZipCodeTyp', 'str:80'),
                    ('EstimatedP', 'float:24.15'),
                    ('LocationTy', 'str:80'),
                    ('ALAND10', 'float:24.15'),
                    ('INTPTLAT10', 'str:80'),
                    ('FUNCSTAT10', 'str:80'),
                    ('Long', 'float:24.15'),
                    ('City', 'str:80'),
                    ('TaxReturns', 'float:24.15'),
                    ('State', 'str:80'),
                    ('Location', 'str:80'),
                    ('GSrchCnt', 'float:24.15'),
                    ('TotalWages', 'float:24.15'),
                    ('Lat', 'float:24.15'),
                    ('MTFCC10', 'str:80'),
                    ('INTPTLON10', 'str:80'),
                    ('GEOID10', 'str:80'),
                    ('Decommisio', 'str:80')]))
        f = next(iter(c))
        assert f['properties']['EstimatedP'] == 27773.0


def test_field_truncation_issue177(tmpdir):
    name = str(tmpdir.join('output.shp'))

    kwargs = {
        'driver': 'ESRI Shapefile',
        'crs': 'EPSG:4326',
        'schema': {
            'geometry': 'Point',
            'properties': [('a_fieldname', 'float')]}}

    with fiona.open(name, 'w', **kwargs) as dst:
        rec = {}
        rec['geometry'] = {'type': 'Point', 'coordinates': (0, 0)}
        rec['properties'] = {'a_fieldname': 3.0}
        dst.write(rec)

    with fiona.open(name) as src:
        first = next(iter(src))
        assert first['geometry'] == {'type': 'Point', 'coordinates': (0, 0)}
        assert first['properties']['a_fieldnam'] == 3.0


def test_unsupported_geometry_type():
    tmpdir = tempfile.mkdtemp()
    tmpfile = os.path.join(tmpdir, 'test-test-geom.shp')

    profile = {
        'driver': 'ESRI Shapefile',
        'schema': {
            'geometry': 'BOGUS',
            'properties': {}}}

    try:
        fiona.open(tmpfile, 'w', **profile)
    except UnsupportedGeometryTypeError:
        assert True


@pytest.mark.parametrize('x', list(range(1, 10)))
def test_normalize_int32(x):
    assert normalize_field_type('int:{}'.format(x)) == 'int32'


@pytest.mark.skipif(get_gdal_version_num() < calc_gdal_version_num(2, 0, 0),
                    reason="64-bit integer fields require GDAL 2+")
@pytest.mark.parametrize('x', list(range(10, 20)))
def test_normalize_int64(x):
    assert normalize_field_type('int:{}'.format(x)) == 'int64'


@pytest.mark.parametrize('x', list(range(0, 20)))
def test_normalize_str(x):
    assert normalize_field_type('str:{}'.format(x)) == 'str'


def test_normalize_bool():
    assert normalize_field_type('bool') == 'bool'


def test_normalize_float():
    assert normalize_field_type('float:25.8') == 'float'


def generate_field_types():
    """
    Produce a unique set of field types in a consistent order.

    This ensures that tests are able to run in parallel.
    """
    types = set(FIELD_TYPES)
    types.remove(None)
    return list(sorted(types)) + [None]


@pytest.mark.parametrize('x', generate_field_types())
def test_normalize_std(x):
    assert normalize_field_type(x) == x


def test_normalize_error():
    with pytest.raises(SchemaError):
        assert normalize_field_type('thingy')
