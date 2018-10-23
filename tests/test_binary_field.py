import fiona

import pytest
import struct
from collections import OrderedDict
from .conftest import requires_gpkg


@requires_gpkg
def test_binary_field(tmpdir):
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

    # create some binary data
    input_data = struct.pack("256B", *range(256))

    # write the binary data to a BLOB field
    filename = str(tmpdir.join("binary_test.gpkg"))
    with fiona.open(filename, "w", **meta) as dst:
        feature = {
            "geometry": {"type": "Point", "coordinates": ((0, 0))},
            "properties": {
                "name": "test",
                u"data": input_data,
            }
        }
        dst.write(feature)

    # read the data back and check consistency
    with fiona.open(filename, "r") as src:
        feature = next(iter(src))
        assert feature["properties"]["name"] == "test"
        output_data = feature["properties"]["data"]
        assert output_data == input_data
