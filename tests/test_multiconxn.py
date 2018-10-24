import pytest

import fiona
from fiona.compat import OrderedDict


class TestReadAccess(object):
    # To check that we'll be able to get multiple 'r' connections to layers
    # in a single file.

    def test_meta(self, path_coutwildrnp_shp):
        with fiona.open(path_coutwildrnp_shp, "r", layer="coutwildrnp") as c:
            with fiona.open(path_coutwildrnp_shp, "r",
                            layer="coutwildrnp") as c2:
                assert len(c) == len(c2)
                assert sorted(c.schema.items()) == sorted(c2.schema.items())

    def test_feat(self, path_coutwildrnp_shp):
        with fiona.open(path_coutwildrnp_shp, "r", layer="coutwildrnp") as c:
            f1 = next(iter(c))
            with fiona.open(path_coutwildrnp_shp, "r",
                            layer="coutwildrnp") as c2:
                f2 = next(iter(c2))
                assert f1 == f2


class TestReadWriteAccess(object):
    # To check that we'll be able to read from a file that we're
    # writing to.

    @pytest.fixture(autouse=True)
    def multi_write_test_shp(self, tmpdir):
        self.shapefile_path = str(tmpdir.join("multi_write_test.shp"))
        self.c = fiona.open(
            self.shapefile_path, "w",
            driver="ESRI Shapefile",
            schema={
                'geometry': 'Point',
                'properties': [('title', 'str:80'), ('date', 'date')]},
            crs={'init': "epsg:4326", 'no_defs': True},
            encoding='utf-8')
        self.f = {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': (0.0, 0.1)},
            'properties': OrderedDict([('title', 'point one'), ('date', '2012-01-29')])}
        self.c.writerecords([self.f])
        self.c.flush()
        yield
        self.c.close()

    def test_meta(self):
        c2 = fiona.open(self.shapefile_path, "r")
        assert len(self.c) == len(c2)
        assert sorted(self.c.schema.items()) == sorted(c2.schema.items())
        c2.close()

    def test_read(self):
        c2 = fiona.open(self.shapefile_path, "r")
        f2 = next(iter(c2))
        del f2['id']
        assert self.f == f2
        c2.close()

    def test_read_after_close(self):
        c2 = fiona.open(self.shapefile_path, "r")
        self.c.close()
        f2 = next(iter(c2))
        del f2['id']
        assert self.f == f2
        c2.close()


class TestLayerCreation(object):
    @pytest.fixture(autouse=True)
    def layer_creation_shp(self, tmpdir):
        self.dir = tmpdir.mkdir('layer_creation')
        self.c = fiona.open(
            str(self.dir), 'w',
            layer='write_test',
            driver='ESRI Shapefile',
            schema={
                'geometry': 'Point',
                'properties': [('title', 'str:80'), ('date', 'date')]},
            crs={'init': "epsg:4326", 'no_defs': True},
            encoding='utf-8')
        self.f = {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': (0.0, 0.1)},
            'properties': OrderedDict([('title', 'point one'), ('date', '2012-01-29')])}
        self.c.writerecords([self.f])
        self.c.flush()
        yield
        self.c.close()

    def test_meta(self):
        c2 = fiona.open(str(self.dir.join("write_test.shp")), "r")
        assert len(self.c) == len(c2)
        assert sorted(self.c.schema.items()) == sorted(c2.schema.items())
        c2.close()

    def test_read(self):
        c2 = fiona.open(str(self.dir.join("write_test.shp")), "r")
        f2 = next(iter(c2))
        del f2['id']
        assert self.f == f2
        c2.close()

    def test_read_after_close(self):
        c2 = fiona.open(str(self.dir.join("write_test.shp")), "r")
        self.c.close()
        f2 = next(iter(c2))
        del f2['id']
        assert self.f == f2
        c2.close()
