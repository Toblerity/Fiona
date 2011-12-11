# -*- coding: utf-8 -*-

"""
Fiona is OGR's neater API – sleek elegance on the outside, unstoppable
OGR(e) on the inside.

Fiona provides a minimal Python interface to the open source GIS
community's most trusted geodata access library and integrates readily
with other Python GIS packages such as pyproj, Rtree and Shapely.
"""

__version__ = "0.3"

from fiona.collection import Collection


def collection(path, mode='r', driver=None, schema=None, crs=None):
    """Open file at ``path`` in ``mode`` "r" (read), "a" (append), or "w"
    (write) and return a ``Collection`` object."""
    if mode == 'r':
        c = Collection(path, mode)
    elif mode in ('a', 'w'):
        c = Collection(path, mode, driver, schema)
    else:
        raise ValueError("Invalid mode: %s" % mode)
    c.open()
    return c

