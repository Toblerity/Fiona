import unittest
import fiona

class SchemaOrder(unittest.TestCase):

    def test_schema_ordering_items(self):
        items = [('title', 'str'), ('date', 'date')]
        with fiona.open('/tmp/test_schema.shp', 'w',
                driver="ESRI Shapefile",
                schema={
                    'geometry': 'LineString', 
                    'properties': items }) as c:
            self.assertEqual(list(c.schema['properties'].items()), items)
        with fiona.open('/tmp/test_schema.shp') as c:
            self.assertEqual(list(c.schema['properties'].items()), items)

