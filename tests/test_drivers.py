"""Tests for Fiona's OGR driver interface."""


import logging
import sys

import pytest
import os
import fiona


logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

GDAL_MAJOR_VER = fiona.get_gdal_version_num() // 1000000

def test_options(tmpdir):
    """Test that setting CPL_DEBUG=ON works"""
    logfile = str(tmpdir.mkdir('tests').join('test_options.log'))
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    with fiona.drivers(CPL_DEBUG=True):
        path = os.path.join("tests", "data", "coutwildrnp.shp")
        c = fiona.open(path)
        c.close()
        with open(logfile, "r") as f:
            log = f.read()
        if GDAL_MAJOR_VER >= 2:
            assert "GDALOpen" in log
        else:
            assert "OGROpen" in log
