
import logging
import os.path
import shutil
import sys
import tempfile

import fiona

def test_options(tmpdir=None):
    """Test that setting CPL_DEBUG=ON works"""
    if tmpdir is None:
        tempdir = tempfile.mkdtemp()
        logfile = os.path.join(tempdir, "example.log")
    else:
        logfile = str(tmpdir.join("example.log"))
    logger = logging.getLogger("Fiona")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    with fiona.drivers(CPL_DEBUG=True):
        c = fiona.open("docs/data/test_uk.shp")
        c.close()
        log = open(logfile).read()
        assert "Option CPL_DEBUG" in log

    if tempdir and tmpdir is None:
        shutil.rmtree(tempdir)
