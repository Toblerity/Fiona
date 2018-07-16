import fiona

import os
import pytest
import unittest
import binascii
import tempfile
import shutil
from collections import OrderedDict
from .conftest import requires_gpkg

class TestBinaryField(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)
    
    @requires_gpkg
    def test_binary_field(self):
        meta = {
            "driver": "GPKG",
            "schema": {
                "geometry": "Point",
                "properties": OrderedDict([
                    ("name", "str"),
                    ("data", "bytes"),
                ])
            }
        }
        
        # create some binary data to encode
        data = binascii.a2b_hex(b"deadbeef")
        
        # write the binary data to a BLOB field
        filename = os.path.join(self.tempdir, "binary_test.gpkg")
        with fiona.open(filename, "w", **meta) as dst:
            feature = {
                "geometry": {"type": "Point", "coordinates": ((0,0))},
                "properties": {
                    "name": "test",
                    "data": data
                }
            }
            dst.write(feature)
        
        del(data)
        
        # read the data back and check consistency
        with fiona.open(filename, "r") as src:
            feature = next(iter(src))
            assert(feature["properties"]["name"] == "test")
            data = feature["properties"]["data"]
            assert(binascii.b2a_hex(data) == b"deadbeef")

if __name__ == "__main__":
    unittest.main()
