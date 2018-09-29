"""Tests for Fiona's OGR driver interface."""


import logging
import os

import pytest

import fiona
from fiona.errors import FionaDeprecationWarning


def test_options(tmpdir):
    """Test that setting CPL_DEBUG=ON works and that a warning is raised."""
    logfile = str(tmpdir.mkdir('tests').join('test_options.log'))
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    # fiona.drivers() will be deprecated.
    with pytest.warns(FionaDeprecationWarning):
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
