# Fiona's date and time is founded on RFC 3339.
#
# OGR knows 3 time "zones": GMT, "local time", amd "unknown". Fiona, when
# writing will convert times with a timezone offset to GMT (Z) and otherwise
# will write times with the unknown zone.

import datetime
import logging
import re

log = logging.getLogger("Fiona")

# Fiona's 'date', 'time', and 'datetime' types are sub types of 'str'.

class FionaDateType(str):
    """Dates without time."""

class FionaTimeType(str):
    """Times without dates."""

class FionaDateTimeType(str):
    """Dates and times."""

pattern_date = re.compile(r"(\d\d\d\d)(-)?(\d\d)(-)?(\d\d)")
pattern_time = re.compile(
    r"(\d\d)(:)?(\d\d)(:)?(\d\d)?(\.\d+)?(Z|([+-])?(\d\d)?(:)?(\d\d))?" )
pattern_datetime = re.compile(
    r"(\d\d\d\d)(-)?(\d\d)(-)?(\d\d)(T)?(\d\d)(:)?(\d\d)(:)?(\d\d)?(\.\d+)?(Z|([+-])?(\d\d)?(:)?(\d\d))?" )

class group_accessor(object):
    def __init__(self, m):
        self.match = m
    def group(self, i):
        try:
            return self.match.group(i) or 0
        except IndexError:
            return 0

def parse_time(text):
    """Given a RFC 3339 time, returns a tz-naive datetime tuple"""
    match = re.search(pattern_time, text)
    if match is None:
        raise ValueError("Time data '%s' does not match pattern" % text)
    g = group_accessor(match)
    log.debug("Match groups: %s", match.groups())
    return (0, 0, 0,
        int(g.group(1)), 
        int(g.group(3)), 
        int(g.group(5)), 
        1000000.0*float(g.group(6)) )

def parse_date(text):
    """Given a RFC 3339 date, returns a tz-naive datetime tuple"""
    match = re.search(pattern_date, text)
    if match is None:
        raise ValueError("Time data '%s' does not match pattern" % text)
    g = group_accessor(match)
    log.debug("Match groups: %s", match.groups())
    return (
        int(g.group(1)), 
        int(g.group(3)), 
        int(g.group(5)),
        0, 0, 0, 0.0 )

def parse_datetime(text):
    """Given a RFC 3339 datetime, returns a tz-naive datetime tuple"""
    match = re.search(pattern_datetime, text)
    if match is None:
        raise ValueError("Time data '%s' does not match pattern" % text)
    g = group_accessor(match)
    log.debug("Match groups: %s", match.groups())
    return (
        int(g.group(1)), 
        int(g.group(3)), 
        int(g.group(5)),
        int(g.group(7)), 
        int(g.group(9)), 
        int(g.group(11)), 
        1000000.0*float(g.group(12)) )

