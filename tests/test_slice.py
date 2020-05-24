"""Note well: collection slicing is deprecated!
"""

import pytest
from fiona.env import GDALVersion
import fiona
from fiona.errors import FionaDeprecationWarning

gdal_version = GDALVersion.runtime()


def test_collection_get(path_coutwildrnp_shp):
    with fiona.open(path_coutwildrnp_shp) as src:
        result = src[5]
        assert result['id'] == '5'


def test_collection_slice(path_coutwildrnp_shp):
    with pytest.warns(FionaDeprecationWarning), fiona.open(path_coutwildrnp_shp) as src:
        results = src[:5]
        assert isinstance(results, list)
        assert len(results) == 5
        assert results[4]['id'] == '4'


def test_collection_iterator_slice(path_coutwildrnp_shp):
    with fiona.open(path_coutwildrnp_shp) as src:
        results = list(src.items(5))
        assert len(results) == 5
        k, v = results[4]
        assert k == 4
        assert v['id'] == '4'


def test_collection_iterator_next(path_coutwildrnp_shp):
    with fiona.open(path_coutwildrnp_shp) as src:
        k, v = next(src.items(5, None))
        assert k == 5
        assert v['id'] == '5'


@pytest.mark.parametrize("args", [(0, 5, None),
                                  (1, 5, None),
                                  (-5, None, None),
                                  (-5, -1, None),
                                  (0, None, None),
                                  (5, None, None),
                                  (0, 5, 2),
                                  (0, 5, 2),
                                  (1, 5, 2),
                                  (-5, None, 2),
                                  (-5, -1, 2),
                                  (0, None, 2),
                                  (0, 8, 2),
                                  (0, 9, 2),
                                  (0, 10, 2),
                                  (1, 8, 2),
                                  (1, 9, 2),
                                  (1, 10, 2),
                                  (1, None, 2),
                                  (5, None, 2),
                                  (5, None, -1),
                                  (5, None, -2),
                                  (5, None, None),
                                  (4, None, -2),
                                  (-1, -5, -1),
                                  (-5, None, -1),
                                  (0, 5, 1),
                                  (5, 15, 1),
                                  (15, 30, 1),
                                  (5, 0, -1),
                                  (15, 5, -1),
                                  (30, 15, -1),
                                  (0, 5, 2),
                                  (5, 15, 2),
                                  (15, 30, 2),
                                  (5, 0, -2),
                                  (15, 5, -2),
                                  (30, 15, -2)
                                  ])
@pytest.mark.filterwarnings('ignore:.*OLC_FASTFEATURECOUNT*')
@pytest.mark.filterwarnings('ignore:.*OLCFastSetNextByIndex*')
def test_collection_iterator_items_slice(slice_dataset, args):
    """ Test if c.items(start, stop, step) returns the correct features.
    """

    start, stop, step = args
    slice_dataset_path, min_id, max_id = slice_dataset

    positions = list(range(min_id, max_id + 1))[start:stop:step]

    with fiona.open(slice_dataset_path, 'r') as c:
        items = list(c.items(start, stop, step))
        assert len(items) == len(positions)
        record_positions = [int(item[1]['properties']['position']) for item in items]
        for expected_position, record_position in zip(positions, record_positions):
            assert expected_position == record_position


def test_collection_iterator_keys_next(path_coutwildrnp_shp):
    with fiona.open(path_coutwildrnp_shp) as src:
        k = next(src.keys(5, None))
        assert k == 5
