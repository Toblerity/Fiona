
import logging
import sys

import fiona

def test_options(tmpdir):
    """Test that setting CPL_DEBUG=ON works"""
    logfile = str(tmpdir.join('example.log'))
    logger = logging.getLogger('Fiona')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    with fiona.drivers(CPL_DEBUG=True):
        c = fiona.open("docs/data/test_uk.shp")
        c.close()
        log = open(logfile).read()
        assert "OGR Error 0: OGR: OGROpen(docs/data/test_uk.shp" in log

