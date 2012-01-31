=====================
The Fiona User Manual
=====================

:Author: Sean Gillies, <sean.gillies@gmail.com>
:Revision: 1.0
:Date: 10 January 2012
:Copyright: 
  This work is licensed under a `Creative Commons Attribution 3.0
  United States License`__.

.. __: http://creativecommons.org/licenses/by/3.0/us/

:Abstract: 
  This document explains how to use the Fiona package for reading and writing
  geospatial data files.

.. sectnum::

.. _intro:

Introduction
============

Fiona is a Python wrapper for the OGR vector data access library. A very simple
wrapper for minimalists. It reads features from files as GeoJSON-like mappings
and writes the same kind of mappings as features back to files. That's it.
There are no layers, no cursors, no geometric operations, no transformations
between coordinate systems. Fiona doesn't just push the complexity of OGR
around, it tries to remove as much of it as possible. Simple to understand and
use, with no gotchas. Vector data access for humans.

Is it Useful?
-------------

Please understand this: Fiona is designed to excel in a certain range of tasks
and is less optimal in others. Fiona trades memory and speed for simplicity and
reliability. Where OGR's Python bindings (for example) use C pointers, Fiona
copies vector data from the data source to Python objects.  These are simpler
and safer to use, but more memory intensive. Fiona's performance is relatively
more slow if you only need access to a single feature property – and of course
if you just want to reproject or filter data files, nothing beats the
``ogr2ogr`` program – but Fiona's performance is much better than OGR's Python
bindings if you want *all* feature data (all properties and all coordinates).
The copying is a constraint, yes, but it simplifies things.  With Fiona, you
don't have to track references to C objects to avoid crashes, and you can work
with feature data using familiar Python mapping accessors.  Less worry, less
time spent reading API documentation.

Guidance
--------

In what cases would you benefit from using Fiona?

* If the features of interest are from or destined for a file in a non-text
  format like ESRI Shapefiles, Mapinfo TAB files, etc.
* If you're more interested in the values of many feature properties than in
  a single property's value.
* If you're more interested in all the coordinate values of a feature's
  geometry than in a single value.
* If your processing system is distributed or not contained to a single
  process.
* If you don't need transactional capability.

In what cases would you not benefit from using Fiona?

* If your data is from or for a GeoJSON document you should use Python's
  ``json`` or ``simplejson``.
* If your data is in a RDBMS like PostGIS, use a Python DB package or ORM like
  ``SQLAlchemy`` or ``GeoAlchemy``. You're probably using GeoDjango in this
  case already, so carry on.
* If your data is served via HTTP from CouchDB or CartoDB, etc, use an HTTP
  package (``httplib2``, ``Requests``, etc) or the provider's Python API.
* If you want to make only small, in situ changes to a shapefile, use
  ``osgeo.ogr``.

Example
-------

The first example of using Fiona is this: copying features from one shapefile
to another, adding two properties and making sure that all feature polygons are
facing "up". Orientation of polygons is significant in some applications,
extruded polygons in Google Earth for one. There's a shapefile in the Fiona
repository that we'll use in this and other examples.

.. sourcecode:: python

  import datetime
  import logging
  import sys
  
  from fiona import collection
  
  
  logging.basicConfig(stream=sys.stderr, level=logging.INFO)
  
  def signed_area(coords):
      """Return the signed area enclosed by a ring using the linear time
      algorithm at http://www.cgafaq.info/wiki/Polygon_Area. A value >= 0
      indicates a counter-clockwise oriented ring.
      """
      xs, ys = map(list, zip(*coords))
      xs.append(xs[1])
      ys.append(ys[1]) 
      return sum(xs[i]*(ys[i+1]-ys[i-1]) for i in range(1, len(coords)))/2.0
  
  
  with collection("docs/data/test_uk.shp", "r") as source:
      
      # Copy the source schema and add two new properties.
      schema = source.schema.copy()
      schema['properties']['s_area'] = 'float'
      schema['properties']['timestamp'] = 'str'
      
      # Create a sink for processed features with the same format and 
      # coordinate reference system as the source.
      with collection(
              "oriented-ccw.shp", "w",
              driver=source.driver,
              schema=schema,
              crs=source.crs
              ) as sink:
          
          for f in source:
              
              try:
  
                  # If any feature's polygon is facing "down" (has rings
                  # wound clockwise), its rings will be reordered to flip
                  # it "up".
                  g = f['geometry']
                  assert g['type'] == "Polygon"
                  rings = g['coordinates']
                  sa = sum(signed_area(r) for r in rings)
                  if sa < 0.0:
                      rings = [r[::-1] for r in rings]
                      g['coordinates'] = rings
                      f['geometry'] = g
  
                  # Add the signed area of the polygon and a timestamp
                  # to the feature properties map.
                  f['properties'].update(
                      s_area=sa,
                      timestamp=datetime.datetime.now().isoformat() )
  
                  sink.write(f)
              
              except Exception, e:
                  logging.exception("Error processing feature %s:", f['id'])

          # The sink collection is written to disk when its block ends

Reading and Writing Data
========================

Only files can be opened as collections.
::

  >>> collection("PG:dbname=databasename", "r")
  Traceback (most recent call last):
    ...
  OSError: Nonexistent path 'PG:dbname=databasename'
  >>> collection(".", "r")
  Traceback (most recent call last):
    ...
  ValueError: Path must be a file


