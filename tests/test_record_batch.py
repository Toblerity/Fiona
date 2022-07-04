"""Record batch API tests."""

import fiona


def test_batch():
    with fiona.open("tests/data/coutwildrnp.shp") as collection:
        assert sum(collection.batches()) == 67
