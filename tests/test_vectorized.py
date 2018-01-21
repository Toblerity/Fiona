import pytest
import fiona
from six import integer_types, string_types
try:
    from fiona._vectorized import read_vectorized
    has_vectorized = True
except ImportError:
    has_vectorized = False

if has_vectorized:
    import numpy as np
    from numpy.testing import assert_allclose

requires_vectorized = pytest.mark.skipif(not has_vectorized, reason="Vectorized submodule not available")

@requires_vectorized
def test_read_vectorized(path_coutwildrnp_shp):
    with fiona.open(path_coutwildrnp_shp, "r") as collection:
        features = read_vectorized(collection)
    
        assert len(features["geometry"]) == 67
        assert features["geometry"].dtype == object
        assert features["geometry"][0].decode("ascii").startswith("POLYGON (")
        assert features["geometry"][-1].decode("ascii").startswith("POLYGON (")
        # TODO: better checks for geometry
        
        # check number of properties
        assert len(features["properties"]) == len(collection.schema["properties"])

        # float
        assert features["properties"]["PERIMETER"].dtype == np.float64
        assert features["properties"]["PERIMETER"].shape == (67,)
        assert_allclose(features["properties"]["PERIMETER"][0], 1.22107)
        assert_allclose(features["properties"]["PERIMETER"][-1], 0.120627)
        
        # integer
        assert features["properties"]["WILDRNP020"].dtype == np.int64
        assert features["properties"]["WILDRNP020"].shape == (67,)
        assert features["properties"]["WILDRNP020"][0] == 332
        assert features["properties"]["WILDRNP020"][-1] == 511
        
        # string
        assert isinstance(features["properties"]["NAME"].dtype, object)
        assert features["properties"]["NAME"].shape == (67,)
        assert features["properties"]["NAME"][0] == "Mount Naomi Wilderness"
        assert features["properties"]["NAME"][-1] == "Mesa Verde Wilderness"
