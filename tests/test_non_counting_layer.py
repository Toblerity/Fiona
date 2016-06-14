import unittest

import fiona

GPX_FILE = 'tests/data/test_gpx.gpx'

class NonCountingLayerTest(unittest.TestCase):
    def setUp(self):
        self.c = fiona.open(GPX_FILE, "r", layer="track_points")
    
    def tearDown(self):
        self.c.close()

    def test_len_fail(self):
        with self.assertRaises(TypeError):
            len(self.c)

    def test_list(self):
        features = list(self.c)
        self.assertEqual(len(features), 19)

    def test_getitem(self):
        feature = self.c[2]

    def test_fail_getitem_negative_index(self):
        with self.assertRaises(IndexError):
            self.c[-1]

    def test_slice(self):
        features = self.c[2:5]
        self.assertEqual(len(features), 3)

    def test_fail_slice_negative_index(self):
        with self.assertRaises(IndexError):
            self.c[2:-4]
