import logging
import sys
import os

import pytest
from packaging.version import parse
import boto3

import fiona
from fiona.vfs import vsi_path, parse_paths

from .test_collection import ReadingTest


# Custom markers (from rasterio)
mingdalversion = pytest.mark.skipif(
    fiona.gdal_version < (2, 1, 0),
    reason="S3 raster access requires GDAL 2.1")

credentials = pytest.mark.skipif(
    not(boto3.Session()._session.get_credentials()),
    reason="S3 raster access requires credentials")


class VsiReadingTest(ReadingTest):
    # There's a bug in GDAL 1.9.2 http://trac.osgeo.org/gdal/ticket/5093
    # in which the VSI driver reports the wrong number of features.
    # I'm overriding ReadingTest's test_filter_1 with a function that
    # passes and creating a new method in this class that we can exclude
    # from the test runner at run time.

    @pytest.mark.xfail(reason="The number of features present in the archive "
                              "differs based on the GDAL version.")
    def test_filter_vsi(self):
        results = list(self.c.filter(bbox=(-114.0, 35.0, -104, 45.0)))
        self.assertEqual(len(results), 67)
        f = results[0]
        self.assertEqual(f['id'], "0")
        self.assertEqual(f['properties']['STATE'], 'UT')


@pytest.mark.usefixtures('uttc_path_coutwildrnp_zip', 'uttc_data_dir')
class ZipReadingTest(VsiReadingTest):

    def setUp(self):
        self.c = fiona.open("zip://{}".format(self.path_coutwildrnp_zip, "r"))
        self.path = os.path.join(self.data_dir, 'coutwildrnp.zip')

    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.assertEqual(
            repr(self.c),
            ("<open Collection '/vsizip/{path}:coutwildrnp', mode 'r' "
            "at {id}>".format(
                id=hex(id(self.c)),
                path=self.path)))

    def test_closed_repr(self):
        self.c.close()
        self.assertEqual(
            repr(self.c),
            ("<closed Collection '/vsizip/{path}:coutwildrnp', mode 'r' "
            "at {id}>".format(
                id=hex(id(self.c)),
                path=self.path)))

    def test_path(self):
        self.assertEqual(
            self.c.path, '/vsizip/{path}'.format(
                path=self.path))


@pytest.mark.usefixtures('uttc_path_coutwildrnp_zip', 'uttc_data_dir')
class ZipArchiveReadingTest(VsiReadingTest):

    def setUp(self):
        vfs = 'zip://{}'.format(self.path_coutwildrnp_zip)
        self.c = fiona.open("/coutwildrnp.shp", "r", vfs=vfs)
        self.path = os.path.join(self.data_dir, 'coutwildrnp.zip')

    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.assertEqual(
            repr(self.c),
            ("<open Collection '/vsizip/{path}/coutwildrnp.shp:coutwildrnp', mode 'r' "
            "at {id}>".format(
                id=hex(id(self.c)),
                path=self.path)))

    def test_closed_repr(self):
        self.c.close()
        self.assertEqual(
            repr(self.c),
            ("<closed Collection '/vsizip/{path}/coutwildrnp.shp:coutwildrnp', mode 'r' "
            "at {id}>".format(
                id=hex(id(self.c)),
                path=self.path)))

    def test_path(self):
        self.assertEqual(
            self.c.path,
            '/vsizip/{path}/coutwildrnp.shp'.format(
                path=self.path))


@pytest.mark.usefixtures('uttc_path_coutwildrnp_zip')
class ZipArchiveReadingTestAbsPath(ZipArchiveReadingTest):

    def setUp(self):
        vfs = 'zip://{}'.format(os.path.abspath(self.path_coutwildrnp_zip))
        self.c = fiona.open("/coutwildrnp.shp", "r", vfs=vfs)

    def test_open_repr(self):
        assert repr(self.c).startswith("<open Collection '/vsizip/")

    def test_closed_repr(self):
        self.c.close()
        assert repr(self.c).startswith("<closed Collection '/vsizip/")

    def test_path(self):
        assert self.c.path.startswith('/vsizip/')


@pytest.mark.usefixtures('uttc_path_coutwildrnp_tar', 'uttc_data_dir')
class TarArchiveReadingTest(VsiReadingTest):

    def setUp(self):
        vfs = "tar://{}".format(self.path_coutwildrnp_tar)
        self.c = fiona.open("/testing/coutwildrnp.shp", "r", vfs=vfs)
        self.path = os.path.join(self.data_dir, 'coutwildrnp.tar')

    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.assertEqual(
            repr(self.c),
            ("<open Collection '/vsitar/{path}/testing/coutwildrnp.shp:coutwildrnp', mode 'r' "
            "at {id}>".format(
                id=hex(id(self.c)),
                path=self.path)))

    def test_closed_repr(self):
        self.c.close()
        self.assertEqual(
            repr(self.c),
            ("<closed Collection '/vsitar/{path}/testing/coutwildrnp.shp:coutwildrnp', mode 'r' "
            "at {id}>".format(
                id=hex(id(self.c)),
                path=self.path)))

    def test_path(self):
        self.assertEqual(
            self.c.path,
            '/vsitar/{path}/testing/coutwildrnp.shp'.format(
                path=self.path))

@pytest.mark.network
def test_open_http():
    ds = fiona.open('https://raw.githubusercontent.com/OSGeo/gdal/master/autotest/ogr/data/poly.shp')
    assert len(ds) == 10


@credentials
@mingdalversion
@pytest.mark.network
def test_open_s3():
    ds = fiona.open('zip+s3://fiona-testing/coutwildrnp.zip')
    assert len(ds) == 67


@pytest.mark.network
def test_open_zip_https():
    ds = fiona.open('zip+https://s3.amazonaws.com/fiona-testing/coutwildrnp.zip')
    assert len(ds) == 67


def test_parse_path():
    assert parse_paths("zip://foo.zip") == ("foo.zip", "zip", None)


def test_parse_path2():
    assert parse_paths("foo") == ("foo", None, None)


def test_parse_vfs():
    assert parse_paths("/", "zip://foo.zip") == ("/", "zip", "foo.zip")
