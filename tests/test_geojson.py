
import logging
import os
import shutil
import sys
import unittest

import fiona
from fiona.collection import supported_drivers
from fiona.errors import FionaValueError, DriverError, SchemaError, CRSError

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class ReadingTest(unittest.TestCase):
    
    def setUp(self):
        self.c = fiona.open('docs/data/test_uk.json', 'r')
    
    def tearDown(self):
        self.c.close()

    def test_json(self):
        self.assertEquals(len(self.c), 48)

