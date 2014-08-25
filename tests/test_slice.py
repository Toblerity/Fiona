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

def test_collection_iterator_keys_next():
    with fiona.open('docs/data/test_uk.shp') as src:
        k = next(src.keys(None, 5))
        assert k == 5
