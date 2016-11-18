import fiona
import os
import shutil
import tempfile
import unittest
from fiona.ogrext import calc_gdal_version_num, get_gdal_version_num

"""

OGR 54bit handling: https://trac.osgeo.org/gdal/wiki/rfc31_ogr_64

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
class TestBigInt(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def testCreateBigIntSchema(self):
        name = os.path.join(self.tempdir, 'output1.shp')

        a_bigint = 10 ** 18 - 1
        fieldname = 'abigint'

        kwargs = {
            'driver': 'ESRI Shapefile',
            'crs': 'EPSG:4326',
            'schema': {
                'geometry': 'Point',
                'properties': [(fieldname, 'int:10')]}}
        if get_gdal_version_num() < calc_gdal_version_num(2, 0, 0):
            with self.assertRaises(OverflowError):
                with fiona.open(name, 'w', **kwargs) as dst:
                    rec = {}
                    rec['geometry'] = {'type': 'Point', 'coordinates': (0, 0)}
                    rec['properties'] = {fieldname: a_bigint}
                    dst.write(rec)
        else:

            with fiona.open(name, 'w', **kwargs) as dst:
                rec = {}
                rec['geometry'] = {'type': 'Point', 'coordinates': (0, 0)}
                rec['properties'] = {fieldname: a_bigint}
                dst.write(rec)

            with fiona.open(name) as src:
                if get_gdal_version_num() >= calc_gdal_version_num(2, 0, 0):
                    first = next(iter(src))
                    self.assertEqual(first['properties'][fieldname], a_bigint)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
