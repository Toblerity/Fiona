import os
import shutil
import tempfile
import unittest
import fiona

class SchemaOrder(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_schema_ordering_items(self):
        items = [('title', 'str'), ('date', 'date')]
        with fiona.open(os.path.join(self.tempdir, 'test_schema.shp'), 'w',
                driver="ESRI Shapefile",
                schema={
                    'geometry': 'LineString', 
                    'properties': items }) as c:
            self.assertEqual(list(c.schema['properties'].items()), items)
        with fiona.open(os.path.join(self.tempdir, 'test_schema.shp')) as c:
            self.assertEqual(list(c.schema['properties'].items()), items)


