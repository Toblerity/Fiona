# -*- coding: utf-8 -*-

"""
Fiona is OGR's neater API – sleek elegance on the outside, unstoppable
OGR(e) on the inside.

Fiona provides a minimal Python interface to the open source GIS
community's most trusted geodata access library and integrates readily
with other Python GIS packages such as pyproj, Rtree and Shapely.

How minimal? Fiona can read features as mappings from shapefiles or
other GIS vector formats and write mappings as features to files using
the same formats. That's all. There aren't any feature or geometry
classes. Features and their geometries are just data.

A Fiona feature is a mapping with `id`, 'geometry`, and `properties`
keys. The value of `id` is a string identifier unique within the
feature's parent collection. The `geometry` is another GeoJSON-like
mapping with `type` and `coordinates` keys. The `properties` of
a feature is another mapping corresponding to its attribute table. For
example:

  {'id': '1',
   'geometry': {'type': 'Point', 'coordinates': (0.0, 0.0)},
   'properties': {'label': 'Null Island'} }

is a Fiona feature with a point geometry and one property. Features are
read and written using objects returned by the ``collection`` function.

Usage
-----

Here's an example of reading a select few UK polygon features from
a shapefile and for each, picking off the first vertex of the exterior
ring of the polygon and using that as the point geometry for a new
feature writing to a "points.shp" file.

  >>> from fiona import collection
  >>> with collection("docs/data/test_uk.shp", "r") as input:
  ...     schema = input.schema.copy()
  ...     schema['geometry'] = 'Point'
  ...     with collection(
  ...             "points.shp", "w", "ESRI Shapefile", schema
  ...             ) as output:
  ...         for f in input.filter(
  ...                 bbox=(-5.0, 55.0, 0.0, 60.0)
  ...                 ):
  ...             value = f['geometry']['coordinates'][0][0]
  ...             f['geometry'] = dict(
  ...                 type='Point', coordinates=value)
  ...             output.write(f)

"""

__version__ = "0.5"

from fiona.collection import Collection


def collection(path, mode='r', driver=None, schema=None, crs=None):
    """Open file at ``path`` in ``mode`` "r" (read), "a" (append), or "w"
    (write) and return a ``Collection`` object.
    
    In append or write mode, a driver name such as "ESRI Shapefile" or
    "GPX" (see OGR docs or ``ogr2ogr --help`` on the command line) and
    a schema mapping such as:
    
      { 'geometry': 'Point', 
        'properties': { 'label': 'str', 'class': 'int', 'value': 'float' } }
        
    must be provided.
    
    The ``crs`` (coordinate reference system) parameter is currently
    ignored.
    
    """
    if mode == 'r':
        c = Collection(path, mode)
    elif mode in ('a', 'w'):
        c = Collection(path, mode, driver, schema)
    else:
        raise ValueError("Invalid mode: %s" % mode)
    c.open()
    return c

