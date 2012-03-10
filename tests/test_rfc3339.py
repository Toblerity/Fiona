# testing Fiona's RFC 3339 support, to be called by nosetests

import logging
import sys
import unittest

from fiona.rfc3339 import parse_date, parse_datetime, parse_time

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

class DateParseTest(unittest.TestCase):

    def test_yyyymmdd(self):
        self.failUnlessEqual(
            parse_date("2012-01-29"), (2012, 1, 29, 0, 0, 0, 0.0))

class TimeParseTest(unittest.TestCase):
    
    def test_hhmmss(self):
        self.failUnlessEqual(
            parse_time("10:11:12"), (0, 0, 0, 10, 11, 12, 0.0))

    def test_hhmm(self):
        self.failUnlessEqual(
            parse_time("10:11"), (0, 0, 0, 10, 11, 0, 0.0))

    def test_hhmmssff(self):
        self.failUnlessEqual(
            parse_time("10:11:12.42"), 
            (0, 0, 0, 10, 11, 12, 0.42*1000000.0))

    def test_hhmmssz(self):
        self.failUnlessEqual(
            parse_time("10:11:12Z"), (0, 0, 0, 10, 11, 12, 0.0))

    def test_hhmmssoff(self):
        self.failUnlessEqual(
            parse_time("10:11:12-01:00"), (0, 0, 0, 10, 11, 12, 0.0))

class DatetimeParseTest(unittest.TestCase):
    
    def test_yyyymmdd(self):
        self.failUnlessEqual(
            parse_datetime("2012-01-29T10:11:12"), 
            (2012, 1, 29, 10, 11, 12, 0.0))


