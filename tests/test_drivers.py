"""Tests for Fiona's OGR driver interface."""


import logging
import sys

import pytest
import os
import fiona


logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


def test_options(tmpdir):
    """Test that setting CPL_DEBUG=ON works"""
    logfile = str(tmpdir.mkdir('tests').join('test_options.log'))
    logger = logging.getLogger('Fiona')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    with fiona.drivers(CPL_DEBUG=True):
        path = os.path.join("tests", "data", "coutwildrnp.shp")
        c = fiona.open(path)
        c.close()
        log = open(logfile).read()
        assert "Option CPL_DEBUG" in log
