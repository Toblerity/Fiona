import logging
import sys

import fiona

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

def test_collection_get():
    with fiona.open('tests/data/coutwildrnp.shp') as src:
        result = src[5]
        assert result['id'] == '5'

def test_collection_slice():
    with fiona.open('tests/data/coutwildrnp.shp') as src:
        results = src[:5]
        assert isinstance(results, list)
        assert len(results) == 5
        assert results[4]['id'] == '4'

def test_collection_iterator_slice():
    with fiona.open('tests/data/coutwildrnp.shp') as src:
        results = list(src.items(5))
        assert len(results) == 5
        k, v = results[4]
        assert k == 4
        assert v['id'] == '4'

def test_collection_iterator_next():
    with fiona.open('tests/data/coutwildrnp.shp') as src:
        k, v = next(src.items(5, None))
        assert k == 5
        assert v['id'] == '5'

def test_collection_iterator_items_slice():

    with fiona.open('tests/data/coutwildrnp.shp') as src:
        l = len(src)

        items = list(src.items(0, 5))
        assert len(items) == 5

        items = list(src.items(1, 5))
        assert len(items) == 4

        items = list(src.items(-5, None))
        assert len(items) == 5

        items = list(src.items(-5, -1))
        assert len(items) == 4

        items = list(src.items(0, None))
        assert len(items) == l

        items = list(src.items(5, None))
        assert len(items) == (l - 5)

        items = list(src.items(5, None, -1))
        assert len(items) == 6

        items = list(src.items(5, None, -2))
        assert len(items) == 3

        items = list(src.items(4, None, -2))
        assert len(items) == 3

        items = list(src.items(-1, -5, -1))
        assert len(items) == 4

        items = list(src.items(-5, None, -1))
        assert len(items) == (l - 5 + 1)

def test_collection_iterator_keys_next():
    with fiona.open('tests/data/coutwildrnp.shp') as src:
        k = next(src.keys(5, None))
        assert k == 5
