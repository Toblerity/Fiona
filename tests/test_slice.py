"""Note well: collection slicing is deprecated!
"""

import logging
import sys

import pytest

import fiona
from fiona.errors import FionaDeprecationWarning

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


def test_collection_iterator_items_slice(path_coutwildrnp_shp):

    with fiona.open(path_coutwildrnp_shp) as src:
        count = len(src)

        items = list(src.items(0, 5))
        assert len(items) == 5

        items = list(src.items(1, 5))
        assert len(items) == 4

        items = list(src.items(-5, None))
        assert len(items) == 5

        items = list(src.items(-5, -1))
        assert len(items) == 4

        items = list(src.items(0, None))
        assert len(items) == count

        items = list(src.items(5, None))
        assert len(items) == (count - 5)

        items = list(src.items(5, None, -1))
        assert len(items) == 6

        items = list(src.items(5, None, -2))
        assert len(items) == 3

        items = list(src.items(4, None, -2))
        assert len(items) == 3

        items = list(src.items(-1, -5, -1))
        assert len(items) == 4

        items = list(src.items(-5, None, -1))
        assert len(items) == (count - 5 + 1)


def test_collection_iterator_keys_next(path_coutwildrnp_shp):
    with fiona.open(path_coutwildrnp_shp) as src:
        k = next(src.keys(5, None))
        assert k == 5
