import logging
import sys

import fiona

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

def test_collection_get():
    with fiona.open('docs/data/test_uk.shp') as src:
        result = src[5]
        assert result['id'] == '5'

def test_collection_slice():
    with fiona.open('docs/data/test_uk.shp') as src:
        results = src[:5]
        assert isinstance(results, list)
        assert len(results) == 5
        assert results[4]['id'] == '4'

def test_collection_iterator_slice():
    with fiona.open('docs/data/test_uk.shp') as src:
        results = list(src.filter(5))
        assert len(results) == 5
        assert results[4]['id'] == '4'

def test_collection_iterator_next():
    with fiona.open('docs/data/test_uk.shp') as src:
        result = next(src.filter(None, 5))
        assert result['id'] == '5'

def test_collection_iterator_items_next():
    with fiona.open('docs/data/test_uk.shp') as src:
        k, v = next(src.items(None, 5))
        assert k == 5
        assert v['id'] == '5'

def test_collection_iterator_items_slice():

    with fiona.open('docs/data/test_uk.shp') as src:
        l = len(src)
        
        items = list(src.items(start=0, stop=5))
        assert len(items) == 5
        
        items = list(src.items(start=1, stop=5))
        assert len(items) == 4

        items = list(src.items(start=-5, stop=None))
        assert len(items) == 5
        
        items = list(src.items(start=-5, stop=-1))
        assert len(items) == 4
        
        items = list(src.items(start=0, stop=None))
        assert len(items) == l

        items = list(src.items(start=5, stop=None))
        assert len(items) == (l - 5)

        items = list(src.items(start=5, step=-1))
        assert len(items) == 6
        
        items = list(src.items(start=5, step=-2))
        assert len(items) == 3

        items = list(src.items(start=4, step=-2))
        assert len(items) == 3
        
        items = list(src.items(start=-1, stop=-5, step=-1))
        assert len(items) == 4
        
        items = list(src.items(start=-5, stop=None, step=-1))
        assert len(items) == (l - 5 + 1)

def test_collection_iterator_keys_next():
    with fiona.open('docs/data/test_uk.shp') as src:
        k = next(src.keys(None, 5))
        assert k == 5
