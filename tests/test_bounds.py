import fiona

def test_bounds():
    with fiona.open("docs/data/test_uk.shp") as src:
        f = next(src)
        assert tuple(round(v, 6) for v in fiona.bounds(f)) == (
                                                         0.735,
                                                         51.357216,
                                                         0.947778,
                                                         51.444717)
        assert tuple(round(v, 6) for v in fiona.bounds(f['geometry'])) == (
                                                         0.735,
                                                         51.357216,
                                                         0.947778,
                                                         51.444717)
