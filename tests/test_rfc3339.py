# testing Fiona's RFC 3339 support, to be called by nosetests

import logging
import re
import sys
import unittest

from fiona.rfc3339 import parse_date, parse_datetime, parse_time
from fiona.rfc3339 import group_accessor, pattern_date

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

class DateParseTest(unittest.TestCase):

    def test_yyyymmdd(self):
        self.assertEqual(
            parse_date("2012-01-29"), (2012, 1, 29, 0, 0, 0, 0.0))

    def test_error(self):
        self.assertRaises(ValueError, parse_date, ("xxx"))

class TimeParseTest(unittest.TestCase):
    
    def test_hhmmss(self):
        self.assertEqual(
            parse_time("10:11:12"), (0, 0, 0, 10, 11, 12, 0.0))

    def test_hhmm(self):
        self.assertEqual(
            parse_time("10:11"), (0, 0, 0, 10, 11, 0, 0.0))

    def test_hhmmssff(self):
        self.assertEqual(
            parse_time("10:11:12.42"), 
            (0, 0, 0, 10, 11, 12, 0.42*1000000.0))

    def test_hhmmssz(self):
        self.assertEqual(
            parse_time("10:11:12Z"), (0, 0, 0, 10, 11, 12, 0.0))

    def test_hhmmssoff(self):
        self.assertEqual(
            parse_time("10:11:12-01:00"), (0, 0, 0, 10, 11, 12, 0.0))

    def test_error(self):
        self.assertRaises(ValueError, parse_time, ("xxx"))

class DatetimeParseTest(unittest.TestCase):
    
    def test_yyyymmdd(self):
        self.assertEqual(
            parse_datetime("2012-01-29T10:11:12"), 
            (2012, 1, 29, 10, 11, 12, 0.0))

    def test_error(self):
        self.assertRaises(ValueError, parse_datetime, ("xxx"))

def test_group_accessor_indexerror():
    match = re.search(pattern_date, '2012-01-29')
    g = group_accessor(match)
    assert g.group(-1) == 0
    assert g.group(6) == 0

