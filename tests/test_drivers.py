"""Tests for Fiona's OGR driver interface."""


import logging
import sys

import pytest

import fiona


logging.basicConfig(stream=sys.stderr, level=logging.INFO)


FIXME_WINDOWS = sys.platform.startswith('win')


@pytest.mark.skipif(
    FIXME_WINDOWS,
    reason="FIXME on Windows. Raises PermissionError Please look into why "
           "this test isn't working.")
def test_options(tmpdir):
    """Test that setting CPL_DEBUG=ON works"""
    logfile = str(tmpdir.mkdir('tests').join('test_options.log'))
    logger = logging.getLogger('Fiona')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    with fiona.drivers(CPL_DEBUG=True):
        c = fiona.open("tests/data/coutwildrnp.shp")
        c.close()
        log = open(logfile).read()
        assert "Option CPL_DEBUG" in log
