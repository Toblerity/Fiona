"""Tests of fiona.env"""

import pytest

import fiona
import fiona.env
from fiona.session import AWSSession


def test_nested_credentials(monkeypatch):
    """Check that rasterio.open() doesn't wipe out surrounding credentials"""

    @fiona.env.ensure_env_with_credentials
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
