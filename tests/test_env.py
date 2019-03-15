"""Tests of fiona.env"""

import os
import sys
try:
    from unittest import mock
except ImportError:
    import mock

import pytest

import fiona
from fiona import _env
from fiona.env import getenv, ensure_env, ensure_env_with_credentials
from fiona.session import AWSSession, GSSession


def test_nested_credentials(monkeypatch):
    """Check that rasterio.open() doesn't wipe out surrounding credentials"""

    @ensure_env_with_credentials
    def fake_opener(path):
        return fiona.env.getenv()

    with fiona.env.Env(session=AWSSession(aws_access_key_id='foo', aws_secret_access_key='bar')):
        assert fiona.env.getenv()['AWS_ACCESS_KEY_ID'] == 'foo'
        assert fiona.env.getenv()['AWS_SECRET_ACCESS_KEY'] == 'bar'

        monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'lol')
        monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'wut')
        gdalenv = fake_opener('s3://foo/bar')
        assert gdalenv['AWS_ACCESS_KEY_ID'] == 'foo'
        assert gdalenv['AWS_SECRET_ACCESS_KEY'] == 'bar'


def test_ensure_env_decorator(gdalenv):
    @ensure_env
    def f():
        return getenv()['FIONA_ENV']
    assert f() is True


def test_ensure_env_decorator_sets_gdal_data(gdalenv, monkeypatch):
    """fiona.env.ensure_env finds GDAL from environment"""
    @ensure_env
    def f():
        return getenv()['GDAL_DATA']

    monkeypatch.setenv('GDAL_DATA', '/lol/wut')
    assert f() == '/lol/wut'


@mock.patch("fiona._env.GDALDataFinder.find_file")
def test_ensure_env_decorator_sets_gdal_data_prefix(find_file, gdalenv, monkeypatch, tmpdir):
    """fiona.env.ensure_env finds GDAL data under a prefix"""
    @ensure_env
    def f():
        return getenv()['GDAL_DATA']

    find_file.return_value = None
    tmpdir.ensure("share/gdal/pcs.csv")
    monkeypatch.delenv('GDAL_DATA', raising=False)
    monkeypatch.setattr(_env, '__file__', str(tmpdir.join("fake.py")))
    monkeypatch.setattr(sys, 'prefix', str(tmpdir))

    assert f() == str(tmpdir.join("share").join("gdal"))


@mock.patch("fiona._env.GDALDataFinder.find_file")
def test_ensure_env_decorator_sets_gdal_data_wheel(find_file, gdalenv, monkeypatch, tmpdir):
    """fiona.env.ensure_env finds GDAL data in a wheel"""
    @ensure_env
    def f():
        return getenv()['GDAL_DATA']

    find_file.return_value = None
    tmpdir.ensure("gdal_data/pcs.csv")
    monkeypatch.delenv('GDAL_DATA', raising=False)
    monkeypatch.setattr(_env, '__file__', str(tmpdir.join(os.path.basename(_env.__file__))))

    assert f() == str(tmpdir.join("gdal_data"))


@mock.patch("fiona._env.GDALDataFinder.find_file")
def test_ensure_env_with_decorator_sets_gdal_data_wheel(find_file, gdalenv, monkeypatch, tmpdir):
    """fiona.env.ensure_env finds GDAL data in a wheel"""
    @ensure_env_with_credentials
    def f(*args):
        return getenv()['GDAL_DATA']

    find_file.return_value = None
    tmpdir.ensure("gdal_data/pcs.csv")
    monkeypatch.delenv('GDAL_DATA', raising=False)
    monkeypatch.setattr(_env, '__file__', str(tmpdir.join(os.path.basename(_env.__file__))))

    assert f("foo") == str(tmpdir.join("gdal_data"))


def test_ensure_env_crs(path_coutwildrnp_shp):
    """Decoration of .crs works"""
    assert fiona.open(path_coutwildrnp_shp).crs


def test_nested_gs_credentials(monkeypatch):
    """Check that rasterio.open() doesn't wipe out surrounding credentials"""

    @ensure_env_with_credentials
    def fake_opener(path):
        return fiona.env.getenv()

    with fiona.env.Env(session=GSSession(google_application_credentials='foo')):
        assert fiona.env.getenv()['GOOGLE_APPLICATION_CREDENTIALS'] == 'foo'

        gdalenv = fake_opener('gs://foo/bar')
        assert gdalenv['GOOGLE_APPLICATION_CREDENTIALS'] == 'foo'
