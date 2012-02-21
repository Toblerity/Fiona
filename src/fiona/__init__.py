# -*- coding: utf-8 -*-

"""
Fiona is OGR's neater API – sleek and elegant on the outside,
indomitable power on the inside.

Fiona provides a minimal, uncomplicated Python interface to the open
source GIS community's most trusted geodata access library and
integrates readily with other Python GIS packages such as pyproj, Rtree
and Shapely.

How minimal? Fiona can read features as mappings from shapefiles or
other GIS vector formats and write mappings as features to files using
the same formats. That's all. There aren't any feature or geometry
classes. Features and their geometries are just data.

A Fiona feature is a Python mapping inspired by the GeoJSON format. It
has `id`, 'geometry`, and `properties` keys. The value of `id` is
a string identifier unique within the feature's parent collection. The
`geometry` is another mapping with `type` and `coordinates` keys. The
`properties` of a feature is another mapping corresponding to its
attribute table. For example:

  {'id': '1',
   'geometry': {'type': 'Point', 'coordinates': (0.0, 0.0)},
   'properties': {'label': u'Null Island'} }

is a Fiona feature with a point geometry and one property. 

Features are read and written using objects returned by the
``collection`` function. These ``Collection`` objects are a lot like
Python ``file`` objects. A ``Collection`` opened in reading mode serves
as an iterator over features. One opened in a writing mode provides
a ``write`` method.

Usage
-----

Here's an example of reading a select few polygon features from
a shapefile and for each, picking off the first vertex of the exterior
ring of the polygon and using that as the point geometry for a new
feature writing to a "points.shp" file.

  >>> from fiona import collection
  >>> with collection("docs/data/test_uk.shp", "r") as input:
  ...     schema = input.schema.copy()
  ...     schema['geometry'] = 'Point'
  ...     with collection(
  ...             "points.shp", "w", "ESRI Shapefile",
  ...             schema=schema, crs=input.crs
  ...             ) as output:
  ...         for f in input.filter(
  ...                 bbox=(-5.0, 55.0, 0.0, 60.0)
  ...                 ):
  ...             value = f['geometry']['coordinates'][0][0]
  ...             f['geometry'] = dict(
  ...                 type='Point', coordinates=value)
  ...             output.write(f)

Because Fiona collections are context managers, they are closed and (in
writing modes) flush contents to disk when their ``with`` blocks end.
"""

__version__ = "0.8"

import os

from fiona.collection import Collection


def collection(path, mode='r', driver=None, schema=None, crs=None):
    
    """Open file at ``path`` in ``mode`` "r" (read), "a" (append), or
    "w" (write) and return a ``Collection`` object.
    
    In write mode, a driver name such as "ESRI Shapefile" or "GPX" (see
    OGR docs or ``ogr2ogr --help`` on the command line) and a schema
    mapping such as:
    
      {'geometry': 'Point', 'properties': { 'class': 'int', 'label':
      'str', 'value': 'float'}}
    
    must be provided. A coordinate reference system for collections in
    write mode can be defined by the ``crs`` parameter. It takes Proj4
    style mappings like
    
      {'proj': 'longlat', 'ellps': 'WGS84', 'datum': 'WGS84', 
       'no_defs': True}
    
    """
    if mode in ('a', 'r'):
        if not os.path.exists(path):
            raise OSError("Nonexistent path '%s'" % path)
        if not os.path.isfile(path):
            raise ValueError("Path must be a file")
        c = Collection(path, mode)
    elif mode == 'w':
        dirname = os.path.dirname(path) or "."
        if not os.path.exists(dirname):
            raise OSError("Nonexistent path '%s'" % path)
        if not driver:
            raise ValueError("An OGR driver name must be specified")
        if not schema:
            raise ValueError("A collection schema must be specified")
        c = Collection(path, mode, driver, schema, crs)
    else:
        raise ValueError("Invalid mode: %s" % mode)
    return c

