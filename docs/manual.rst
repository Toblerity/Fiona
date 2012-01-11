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

Yes. But understand that Fiona is geared to excel in a certain range of tasks
and isn't going to be optimal for others. Fiona trades memory and speed for
simplicity and reliability. It copies vector data from the data source to
Python objects, where OGR's Python bindings use C pointers. The Python objects
are simpler and safer to use, but more memory intensive. Fiona's performance is
relatively more slow if you only need access to a single feature property – and
of course if you just want to reproject or filter data files, nothing beats the
``ogr2ogr`` program – but Fiona's performance is much better than OGR's Python
bindings if you want *all* feature data (all properties and all coordinates).
The copying is a constraint, yes, but it simplifies things. With Fiona, you
don't have to track references to C objects to avoid crashes, and you can work
with feature data using familiar Python mapping accessors. Less worry, less
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

The canonical example for Fiona is this: copying from one shapefile to another,
through a spatial filter, and making a trivial transformation of feature
geometry.

.. sourcecode:: python

  from fiona import collection

  # Open a source of features
  with collection("docs/data/test_uk.shp", "r") as source:
  
      # Define a schema for the feature sink
      schema = source.schema.copy()
      schema['geometry'] = 'Point'
      
      # Open a new sink for features
      with collection(
              "test_write.shp", "w",
              driver=source.driver, 
              schema=schema, 
              crs=source.crs
              ) as sink:
          
          # Process only the features intersecting a box
          for f in source.filter(bbox=(-5.0, 55.0, 0.0, 60.0)):
          
              # Get point on the boundary of the feature
              f['geometry'] = f['geometry'] = {
                  'type': 'Point',
                  'coordinates': f['geometry']['coordinates'][0][0] }
              
              # Stage feature for writing
              sink.write(f)
              
      # The sink shapefile is written to disk when its ``with`` block ends

Reading and Writing Data
========================

TODO.

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


