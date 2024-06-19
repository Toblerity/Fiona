"""Tests of the Python opener VSI plugin."""

import io

import fsspec
import pytest

import fiona
from fiona.model import Feature


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


def test_opener_fsspec_fs_write(tmp_path):
    """Write a feature via an fsspec fs opener."""
    schema = {"geometry": "Point", "properties": {"zero": "int"}}
    feature = Feature.from_dict(
        **{
            "geometry": {"type": "Point", "coordinates": (0, 0)},
            "properties": {"zero": "0"},
        }
    )
    fs = fsspec.filesystem("file")
    outputfile = tmp_path.joinpath("test.shp")

    with fiona.open(
        str(outputfile),
        "w",
        driver="ESRI Shapefile",
        schema=schema,
        crs="OGC:CRS84",
        opener=fs,
    ) as collection:
        collection.write(feature)
        assert len(collection) == 1
        assert collection.crs == "OGC:CRS84"
