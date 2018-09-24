"""Tests for Fiona's OGR driver interface."""


import logging
import os

import pytest

import fiona


def test_options(tmpdir):
    """Test that setting CPL_DEBUG=ON works"""
    logfile = str(tmpdir.mkdir('tests').join('test_options.log'))
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    with pytest.warns(UserWarning):
        with fiona.drivers(CPL_DEBUG=True):
            path = os.path.join("tests", "data", "coutwildrnp.shp")
            c = fiona.open(path)
            c.close()
            with open(logfile, "r") as f:
                log = f.read()
            if fiona.gdal_version.major >= 2:
                assert "GDALOpen" in log
            else:
                assert "OGROpen" in log
