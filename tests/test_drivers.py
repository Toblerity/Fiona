import logging
import os.path
import shutil
import sys
import tempfile
import unittest

import fiona


logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

FIXME_WINDOWS = sys.platform.startswith('win')

@unittest.skipIf(FIXME_WINDOWS, 
                 reason="FIXME on Windows. Raises PermissionError Please look into why this test isn't working.")
def test_options(tmpdir=None):
    """Test that setting CPL_DEBUG=ON works"""
    if tmpdir is None:
        tempdir = tempfile.mkdtemp()
        logfile = os.path.join(tempdir, 'example.log')
    else:
        logfile = str(tmpdir.join('example.log'))
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

    if tempdir and tmpdir is None:
        shutil.rmtree(tempdir)
