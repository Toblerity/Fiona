"""Tests of the Python opener VSI plugin."""

import io

import fsspec
import pytest

import fiona


def test_opener_io_open(path_grenada_geojson):
    """Use io.open as opener."""
    with fiona.open(path_grenada_geojson, opener=io.open) as colxn:
        profile = colxn.profile
        assert profile["driver"] == "GeoJSON"
        assert len(colxn) == 1


def test_opener_fsspec_zip_fs():
    """Use fsspec zip filesystem as opener."""
    fs = fsspec.filesystem("zip", fo="tests/data/coutwildrnp.zip")
    with fiona.open("coutwildrnp.shp", opener=fs) as colxn:
        profile = colxn.profile
        assert profile["driver"] == "ESRI Shapefile"
        assert len(colxn) == 67
        assert colxn.schema["geometry"] == "Polygon"
        assert "AGBUR" in colxn.schema["properties"]


def test_opener_fsspec_zip_http_fs():
    """Use fsspec zip+http filesystem as opener."""
    fs = fsspec.filesystem(
        "zip",
        target_protocol="http",
        fo="https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip",
    )
    with fiona.open("coutwildrnp.shp", opener=fs) as colxn:
        profile = colxn.profile
        assert profile["driver"] == "ESRI Shapefile"
        assert len(colxn) == 67
        assert colxn.schema["geometry"] == "Polygon"
        assert "AGBUR" in colxn.schema["properties"]


def test_opener_tiledb_file():
    """Use tiledb vfs as opener."""
    tiledb = pytest.importorskip("tiledb")
    fs = tiledb.VFS()
    with fiona.open("tests/data/coutwildrnp.shp", opener=fs) as colxn:
        profile = colxn.profile
        assert profile["driver"] == "ESRI Shapefile"
        assert len(colxn) == 67
        assert colxn.schema["geometry"] == "Polygon"
        assert "AGBUR" in colxn.schema["properties"]
