=====================
The Fiona User Manual
=====================

:Author: Sean Gillies, <sean.gillies@gmail.com>
:Revision: 1.0
:Date: 4 February 2012
:Copyright: 
  This work is licensed under a `Creative Commons Attribution 3.0
  United States License`__.

.. __: http://creativecommons.org/licenses/by/3.0/us/

:Abstract:
  Fiona is OGR's neater API. This document explains how to use the Fiona
  package for reading and writing geospatial data files.

.. sectnum::

.. _intro:

Introduction
============

The data in geographic information systems (GIS) is roughly divided into
rasters representing continuous scalar fields (land surface temperature or
elevation, for example) and vectors representing discrete entities like roads
and administrative boundaries. Concerned exclusively with the latter, Fiona is
a Python wrapper for vector data access functions from the OGR_ library. A very
simple wrapper for minimalists. It reads data records from files as
GeoJSON-like mappings and writes the same kind of mappings as records back to
files. That's it. There are no layers, no cursors, no geometric operations, no
transformations between coordinate systems, no remote method calls; all these
concerns are left to other Python packages such as Shapely_ and pyproj_ and
Python language protocols. Why? To eliminate unnecessary complication. Fiona is
simple to understand and use, with no gotchas.

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

In what cases would you not benefit from using Fiona?

* If your data is in or destined for a JSON document you should use Python's
  ``json`` or ``simplejson``.
* If your data is in a RDBMS like PostGIS, use a Python DB package or ORM like
  ``SQLAlchemy`` or ``GeoAlchemy``. Maybe you're using GeoDjango in this
  already. If so, carry on.
* If your data is served via HTTP from CouchDB or CartoDB, etc, use an HTTP
  package (``httplib2``, ``Requests``, etc) or the provider's Python API.
* If you want to make only small, in situ changes to a shapefile, use
  ``osgeo.ogr``.
* If you can use ``ogr2ogr``, do so.

Example
-------

The first example of using Fiona is this: copying records from one shapefile
to another, adding two attributes and making sure that all polygons are
facing "up". Orientation of polygons is significant in some applications,
extruded polygons in Google Earth for one. No other library (like Shapely) is
needed here, which keeps it uncomplicated. There's a shapefile in the Fiona
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

.. _OGR: http://www.gdal.org/ogr/
.. _pyproj: http://code.google.com/p/pyproj/
.. _Shapely: https://github.com/Toblerity/Shapely

Data Model
==========

Discrete geographic features are usually represented in geographic information
systems by records. The characteristics of records and their semantic
implications are well known [Kent1978]_. Among those most significant for
geographic data: records have a single type, all records of that type have the
same fields, and a record's fields concern a single geographic feature.
Different systems model records in different ways, but the various models have
enough in common that programmers have been able to create useful abstract data
models.  The `OGR model <http://www.gdal.org/ogr/ogr_arch.html>`__ is one. Its
primary entities are `Data Sources`, `Layers`, and `Features`. Features have
not fields, but attributes and a `Geometry`. An OGR Layer contains Features (or
records) of a single type ("roads" or "wells", for example). The [GeoJSON]_
model is a bit more simple, keeping `Features` and substituting `Feature
Collections` for OGR Data Sources and Layers. The term "Feature" is thus
overloaded in GIS modeling, denoting entities in both our conceptual and
data models.

Various formats for record files exist. The Shapefile [ESRI1998]_ has been, at
least in the United States, the most significant of these up to about 2005 and
remains popular today. It is a binary format. The shape fields are stored in
one .shp file and the other fields in another .dbf file. The [GeoJSON]_ format,
from 2008, proposed a human readable text format in which geometry and other
attribute fields are encoded together using Javascript Object Notation [JSON]_.
In GeoJSON, there's a uniformity of data access. Attributes of features are
accessed in the same manner as attributes of a feature collection. Coordinates
of a geometry are accessed in the same manner as features of a collection.

The GeoJSON format turns out to be a good model for a Python API. JSON objects
and Python dictionaries are very syntactically similar. Replacing
object-oriented Layer and Feature APIs with interfaces based on Python mappings
provides a uniformity of access to data and reduces the amount of time spent
reading documentation. A Python programmer knows how to use a mapping, so why
not treat features as dictionaries? Use of existing Python idioms is one of
Fiona's major design principles.

Fiona subscribes to the conventional record model of data, but provides
GeoJSON-like access to the data via Python file-like and mapping protocols.

Reading from Collections
========================

A GIS file is read by opening it in mode "r" using the `collection` function.

.. sourcecode:: pycon

  >>> from fiona import collection
  >>> c = collection("docs/data/test_uk.shp", "r")
  >>> c.opened
  True

It's a bit like a Python ``file``, but instead of reading lines via an iterator, you read features.

.. sourcecode:: pycon

  >>> features = list(c)
  >>> len(features)
  48

Python's ``list()`` function iterates over the entire collection. Try it again 
and you'll see that it's emptied.

.. sourcecode:: pycon

  >>> list(c)
  []

Attributes
----------

The mode the file was opened in ...

.. sourcecode:: pycon

  >>> c.mode
  'r'

The name of the OGR driver used to open the file ...

.. sourcecode:: pycon

  >>> c.driver
  'ESRI Shapefile'

The coordinate reference system of the file ...

.. sourcecode:: pycon

  >>> c.crs
  {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

And finally, the schema of the file, a description of the geometries and
attributes of all its records.

.. sourcecode:: pycon

  >>> import pprint
  >>> pprint.pprint(c.schema)
  {'geometry': 'Polygon',
   'properties': {'AREA': 'float',
                  'CAT': 'float',
                  'CNTRY_NAME': 'str',
                  'FIPS_CNTRY': 'str',
                  'POP_CNTRY': 'float'}}



  >>> collection("PG:dbname=databasename", "r")
  Traceback (most recent call last):
    ...
  OSError: Nonexistent path 'PG:dbname=databasename'
  >>> collection(".", "r")
  Traceback (most recent call last):
    ...
  ValueError: Path must be a file


.. [Kent1978] William Kent, Data and Reality, North Holland, 1978.
.. [ESRI1998] ESRI Shapefile Technical Description. July 1998. http://www.esri.com/library/whitepapers/pdfs/shapefile.pdf
.. [GeoJSON] http://geojson.org
.. [JSON] http://www.ietf.org/rfc/rfc4627

