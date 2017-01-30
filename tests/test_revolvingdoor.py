# Test of opening and closing and opening

import logging
import os.path
import shutil
import subprocess
import sys
import tempfile
import unittest

import fiona

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
log = logging.getLogger('fiona.tests')

class RevolvingDoorTest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_write_revolving_door(self):

        with fiona.open('tests/data/coutwildrnp.shp') as src:
            meta = src.meta
            features = list(src)

        shpname = os.path.join(self.tempdir, 'foo.shp')
        
        with fiona.open(shpname, 'w', **meta) as dst:
            dst.writerecords(features)

        with fiona.open(shpname) as src:
            pass
