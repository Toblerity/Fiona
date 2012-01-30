# testing Fiona's RFC 3339 support, to be called by nosetests

import logging
import sys
import unittest

from fiona.rfc3339 import parse_date, parse_datetime, parse_time

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

class DateParseTest(unittest.TestCase):
    
    def test_yyyymmdd(self):
        y, m, d, hh, mm, ss, ff = parse_date("2012-01-29")
        self.failUnlessEqual(y, 2012)
        self.failUnlessEqual(m, 1)
        self.failUnlessEqual(d, 29)
        self.failUnlessEqual(hh, 0)

class TimeParseTest(unittest.TestCase):
    
    def test_hhmmss(self):
        y, m, d, hh, mm, ss, ff = parse_time("10:11:12")
        self.failUnlessEqual(y, 0)
        self.failUnlessEqual(hh, 10)
        self.failUnlessEqual(mm, 11)
        self.failUnlessEqual(ss, 12)
        self.failUnlessEqual(ff, 0.0)

    def test_hhmm(self):
        y, m, d, hh, mm, ss, ff = parse_time("10:11")
        self.failUnlessEqual(y, 0)
        self.failUnlessEqual(hh, 10)
        self.failUnlessEqual(mm, 11)
        self.failUnlessEqual(ss, 0)
        self.failUnlessEqual(ff, 0.0)

    def test_hhmmssff(self):
        y, m, d, hh, mm, ss, ff = parse_time("10:11:12.42")
        self.failUnlessEqual(y, 0)
        self.failUnlessEqual(hh, 10)
        self.failUnlessEqual(mm, 11)
        self.failUnlessEqual(ss, 12)
        self.failUnlessEqual(ff, 0.42*1000000.0)

    def test_hhmmssz(self):
        y, m, d, hh, mm, ss, ff = parse_time("10:11:12Z")
        self.failUnlessEqual(y, 0)
        self.failUnlessEqual(hh, 10)
        self.failUnlessEqual(mm, 11)
        self.failUnlessEqual(ss, 12)
        self.failUnlessEqual(ff, 0.0)

    def test_hhmmssoff(self):
        y, m, d, hh, mm, ss, ff = parse_time("10:11:12-01:00")
        self.failUnlessEqual(y, 0)
        self.failUnlessEqual(hh, 10)
        self.failUnlessEqual(mm, 11)
        self.failUnlessEqual(ss, 12)
        self.failUnlessEqual(ff, 0.0)

class DatetimeParseTest(unittest.TestCase):
    
    def test_yyyymmdd(self):
        y, m, d, hh, mm, ss, ff = parse_datetime("2012-01-29T10:11:12")
        self.failUnlessEqual(y, 2012)
        self.failUnlessEqual(m, 1)
        self.failUnlessEqual(d, 29)
        self.failUnlessEqual(hh, 10)
        self.failUnlessEqual(mm, 11)
        self.failUnlessEqual(ss, 12)
        self.failUnlessEqual(ff, 0.0)


