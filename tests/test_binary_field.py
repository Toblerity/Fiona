import fiona

import os
import pytest
import unittest
import binascii
import tempfile
import shutil
from collections import OrderedDict
from .conftest import requires_gpkg

def write_binary_gpkg(path):
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
    with fiona.open(path, "w", **meta) as dst:
        feature = {
            "geometry": {"type": "Point", "coordinates": ((0,0))},
            "properties": {
                "name": "test",
                "data": data
            }
        }
        dst.write(feature)


class TestBinaryField(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)
    
    @requires_gpkg
    def test_binary_field(self):
        filename = os.path.join(self.tempdir, "binary_test.gpkg")

        write_binary_gpkg(filename)
        
        # read the data back and check consistency
        with fiona.open(filename, "r") as src:
            feature = next(src)
            assert(feature["properties"]["name"] == "test")
            data = feature["properties"]["data"]
            assert(binascii.b2a_hex(data) == b"deadbeef")

if __name__ == "__main__":
    unittest.main()
