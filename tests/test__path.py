"""_path tests."""

import sys

from fiona._path import _parse_path, _vsi_path


def test_parse_zip_windows(monkeypatch):
    """Parse a zip+ Windows path."""
    monkeypatch.setattr(sys, "platform", "win32")
    path = _parse_path("zip://D:\\a\\Fiona\\Fiona\\tests\\data\\coutwildrnp.zip!coutwildrnp.shp")
    vsi_path = _vsi_path(path)
    assert vsi_path == "/vsizip/D:\\a\\Fiona\\Fiona\\tests\\data\\coutwildrnp.zip/coutwildrnp.shp"
