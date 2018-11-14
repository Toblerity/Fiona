"""OGR 64bit handling: https://trac.osgeo.org/gdal/wiki/rfc31_ogr_64

Shapefile: OFTInteger fields are created by default with a width of 9
characters, so to be unambiguously read as OFTInteger (and if specifying
integer that require 10 or 11 characters. the field is dynamically extended
like managed since a few versions). OFTInteger64 fields are created by default
with a width of 18 digits, so to be unambiguously read as OFTInteger64, and
extented to 19 or 20 if needed. Integer fields of width between 10 and 18
will be read as OFTInteger64. Above they will be treated as OFTReal. In
previous GDAL versions, Integer fields were created with a default with of 10,
and thus will be now read as OFTInteger64. An open option, DETECT_TYPE=YES, can
be specified so as OGR does a full scan of the DBF file to see if integer
fields of size 10 or 11 hold 32 bit or 64 bit values and adjust the type
accordingly (and same for integer fields of size 19 or 20, in case of overflow
of 64 bit integer, OFTReal is chosen)
"""

import pytest

import fiona
from fiona.env import calc_gdal_version_num, get_gdal_version_num


@pytest.mark.xfail(fiona.gdal_version.major < 2,
                   reason="64-bit integer fields require GDAL 2+")
def testCreateBigIntSchema(tmpdir):
    name = str(tmpdir.join('output1.shp'))

    a_bigint = 10 ** 18 - 1
    fieldname = 'abigint'

    kwargs = {
        'driver': 'ESRI Shapefile',
        'crs': 'EPSG:4326',
        'schema': {
            'geometry': 'Point',
            'properties': [(fieldname, 'int:10')]}}

    with fiona.open(name, 'w', **kwargs) as dst:
        rec = {}
        rec['geometry'] = {'type': 'Point', 'coordinates': (0, 0)}
        rec['properties'] = {fieldname: a_bigint}
        dst.write(rec)

    with fiona.open(name) as src:
        if fiona.gdal_version >= (2, 0, 0):
            first = next(iter(src))
            assert first['properties'][fieldname] == a_bigint


@pytest.mark.skipif(get_gdal_version_num() < calc_gdal_version_num(2, 0, 0),
                    reason="Test requires GDAL 2+")
@pytest.mark.parametrize('dtype', ['int', 'int64'])
def test_issue691(tmpdir, dtype):
    """Type 'int' maps to 'int64'"""
    schema = {'geometry': 'Any', 'properties': {'foo': dtype}}
    with fiona.open(
            str(tmpdir.join('test.shp')), 'w', driver='Shapefile',
            schema=schema, crs='epsg:4326') as dst:
        dst.write({
            'type': 'Feature',
            'geometry': {'type': 'Point',
                         'coordinates': (-122.278015, 37.868995)},
            'properties': {'foo': 3694063472}})

    with fiona.open(str(tmpdir.join('test.shp'))) as src:
        assert src.schema['properties']['foo'] == 'int:18'
        first = next(iter(src))
        assert first['properties']['foo'] == 3694063472
