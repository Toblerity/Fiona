import fiona


def test_bounds_point():
    g = {'type': 'Point', 'coordinates': [10, 10]}
    assert fiona.bounds(g) == (10, 10, 10, 10)


def test_bounds_line():
    g = {'type': 'LineString', 'coordinates': [[0, 0], [10, 10]]}
    assert fiona.bounds(g) == (0, 0, 10, 10)


def test_bounds_polygon():
    g = {'type': 'Polygon', 'coordinates': [[[0, 0], [10, 10], [10, 0]]]}
    assert fiona.bounds(g) == (0, 0, 10, 10)


def test_bounds_z():
    g = {'type': 'Point', 'coordinates': [10,10,10]}
    assert fiona.bounds(g) == (10, 10, 10, 10)
