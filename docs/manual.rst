=====================
The Fiona User Manual
=====================

:Author: Sean Gillies, <sean.gillies@gmail.com>
:Version: |release|
:Date: |today|
:Copyright: 
  This work is licensed under a `Creative Commons Attribution 3.0
  United States License`__.

.. __: http://creativecommons.org/licenses/by/3.0/us/

:Abstract:
  Fiona is OGR's neat, nimble, no-nonsense API. This document explains how to
  use the Fiona package for reading and writing geospatial data files.

.. sectnum::

.. _intro:

Introduction
============

:dfn:`Geographic information systems` (GIS) help us plan, react to, and
understand changes in our physical, political, economic, and cultural
landscapes. A generation ago, GIS was something done only by major institutions
like nations and cities, but it's become ubiquitous today thanks to accurate
and inexpensive global positioning systems, commoditization of satellite
imagery, and open source software.

The kinds of data in GIS are roughly divided into :dfn:`rasters` representing
continuous scalar fields (land surface temperature or elevation, for example)
and :dfn:`vectors` representing discrete entities like roads and administrative
boundaries. Fiona is concerned exclusively with the latter. It is a Python
wrapper for vector data access functions from the `OGR
<http://www.gdal.org/ogr/>`_ library.  A very simple wrapper for minimalists.
It reads data records from files as GeoJSON-like mappings and writes the same
kind of mappings as records back to files. That's it. There are no layers, no
cursors, no geometric operations, no transformations between coordinate
systems, no remote method calls; all these concerns are left to other Python
packages such as :py:mod:`Shapely <https://github.com/Toblerity/Shapely>` and
:py:mod:`pyproj <http://code.google.com/p/pyproj/>` and Python language
protocols. Why? To eliminate unnecessary complication. Fiona aims to be simple
to understand and use, with no gotchas.

Please understand this: Fiona is designed to excel in a certain range of tasks
and is less optimal in others. Fiona trades memory and speed for simplicity and
reliability. Where OGR's Python bindings (for example) use C pointers, Fiona
copies vector data from the data source to Python objects.  These are simpler
and safer to use, but more memory intensive. Fiona's performance is relatively
more slow if you only need access to a single record field – and of course if
you just want to reproject or filter data files, nothing beats the
:command:`ogr2ogr` program – but Fiona's performance is much better than OGR's
Python bindings if you want *all* fields and coordinates of a record. The
copying is a constraint, but it simplifies programs. With Fiona, you don't have
to track references to C objects to avoid crashes, and you can work with vector
data using familiar Python mapping accessors. Less worry, less time spent
reading API documentation.

Rules of Thumb
--------------

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
  :py:mod:`json` or :py:mod:`simplejson` modules.
* If your data is in a RDBMS like PostGIS, use a Python DB package or ORM like
  :py:mod:`SQLAlchemy` or :py:mod:`GeoAlchemy`. Maybe you're using
  :py:mod:`GeoDjango` already. If so, carry on.
* If your data is served via HTTP from CouchDB or CartoDB, etc, use an HTTP
  package (:py:mod:`httplib2`, :py:mod:`Requests`, etc) or the provider's
  Python API.
* If you can use :command:`ogr2ogr`, do so.

Example
-------

The first example of using Fiona is this: copying records from one file to
another, adding two attributes and making sure that all polygons are facing
"up". Orientation of polygons is significant in some applications, extruded
polygons in Google Earth for one. No other library (like :py:mod:`Shapely`) is
needed here, which keeps it uncomplicated. There's a :file:`test_uk` file in
the Fiona repository for use in this and other examples.

.. sourcecode:: python

  import datetime
  import logging
  import sys
  
  import fiona
  
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
  
  with fiona.open('docs/data/test_uk.shp', 'r') as source:
      
      # Copy the source schema and add two new properties.
      sink_schema = source.schema.copy()
      sink_schema['properties']['s_area'] = 'float'
      sink_schema['properties']['timestamp'] = 'datetime'
      
      # Create a sink for processed features with the same format and 
      # coordinate reference system as the source.
      with fiona.open(
              'oriented-ccw.shp', 'w',
              crs=source.crs,
              driver=source.driver,
              schema=sink_schema,
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

          # The sink file is written to disk and closed when its block ends.

Data Model
==========

Discrete geographic features are usually represented in geographic information
systems by :dfn:`records`. The characteristics of records and their semantic
implications are well known [Kent1978]_. Among those most significant for
geographic data: records have a single type, all records of that type have the
same fields, and a record's fields concern a single geographic feature.
Different systems model records in different ways, but the various models have
enough in common that programmers have been able to create useful abstract data
models.  The `OGR model <http://www.gdal.org/ogr/ogr_arch.html>`__ is one. Its
primary entities are :dfn:`Data Sources`, :dfn:`Layers`, and :dfn:`Features`.
Features have not fields, but attributes and a :dfn:`Geometry`. An OGR Layer
contains Features of a single type ("roads" or "wells", for example). The
GeoJSON model is a bit more simple, keeping Features and substituting
:dfn:`Feature Collections` for OGR Data Sources and Layers. The term "Feature"
is thus overloaded in GIS modeling, denoting entities in both our conceptual
and data models.

Various formats for record files exist. The :dfn:`ESRI Shapefile` [ESRI1998]_
has been, at least in the United States, the most significant of these up to
about 2005 and remains popular today. It is a binary format. The shape fields
are stored in one .shp file and the other fields in another .dbf file. The
GeoJSON [GeoJSON]_ format, from 2008, proposed a human readable text format in
which geometry and other attribute fields are encoded together using
:dfn:`Javascript Object Notation` [JSON]_. In GeoJSON, there's a uniformity of
data access.  Attributes of features are accessed in the same manner as
attributes of a feature collection.  Coordinates of a geometry are accessed in
the same manner as features of a collection.

The GeoJSON format turns out to be a good model for a Python API. JSON objects
and Python dictionaries are semantically and syntactically similar. Replacing
object-oriented Layer and Feature APIs with interfaces based on Python mappings
provides a uniformity of access to data and reduces the amount of time spent
reading documentation. A Python programmer knows how to use a mapping, so why
not treat features as dictionaries? Use of existing Python idioms is one of
Fiona's major design principles.

.. admonition:: TL;DR
   
   Fiona subscribes to the conventional record model of data, but provides
   GeoJSON-like access to the data via Python file-like and mapping protocols.

Reading Vector Data
===================

Reading a GIS vector file begins by opening it in mode ``'r'`` using Fiona's
:py:func:`~fiona.open` function. It returns an opened
:py:class:`~fiona.collection.Collection` object.

.. sourcecode:: pycon

  >>> import fiona
  >>> c = fiona.open('docs/data/test_uk.shp', 'r')
  >>> c
  <open Collection 'docs/data/test_uk.shp:test_uk', mode 'r' at 0x3763d0>
  >>> c.closed
  False

.. admonition:: API Change

   :py:func:`fiona.collection` is deprecated, but aliased to 
   :py:func:`fiona.open` in version 0.9.

Fiona's :py:class:`~fiona.collection.Collection` is like a Python
:py:class:`file`, but is iterable for records rather than lines.

.. sourcecode:: pycon

  >>> next(c)
  {'geometry': {'type': 'Polygon', 'coordinates': ...
  >>> len(list(c))
  47

Note that :py:func:`list` iterates over the entire collection, effectively
emptying it as with a Python :py:class:`file`.

.. sourcecode:: pycon

  >>> next(c)
  Traceback (most recent call last):
  ...
  StopIteration
  >>> len(list(c))
  0

Seeking the beginning of the file is not supported. You must reopen the
collection to get back to the beginning.

.. sourcecode:: pycon

  >>> c = fiona.open('docs/data/test_uk.shp', 'r')
  >>> len(list(c))
  48

.. admonition:: File Encoding

   The format drivers will attempt to detect the encoding of your data, but may
   fail. In my experience GDAL 1.7.2 (for example) doesn't detect that the
   encoding of the Natural Earth dataset is Windows-1252. In this case, the
   proper encoding can be specified explicitly by using the ``encoding``
   keyword parameter of :py:func:`fiona.open`: ``encoding='Windows-1252'``.
   
   New in version 0.9.1.

Filtering
---------

With some vector data formats a spatial index accompanies the data file,
allowing efficient bounding box searches. A collection's
:py:meth:`~fiona.collection.Collection.filter` method returns an iterator over
records that intersect a given ``(minx, miny, maxx, maxy)`` bounding box. The
collection's own coordinate reference system (see below) is used to interpret
the box's values.

.. sourcecode:: pycon

  >>> c = fiona.open('docs/data/test_uk.shp', 'r')
  >>> hits = c.filter(bbox=(-5.0, 55.0, 0.0, 60.0))
  >>> len(list(hits))
  7

Closing Files
-------------

A :py:class:`~fiona.collection.Collection` involves external resources. There's
no guarantee that these will be released unless you explictly
:py:meth:`~fiona.collection.Collection.close` the object or use
a :keyword:`with` statement. When a :py:class:`~fiona.collection.Collection` is
a context guard, it is closed no matter what happens within the block.

.. sourcecode:: pycon

  >>> try:
  ...     with fiona.open('docs/data/test_uk.shp', 'r') as c:
  ...         print len(list(c))
  ...         assert True is False
  ... except:
  ...     print c.closed
  ...     raise
  ... 
  48
  True
  Traceback (most recent call last):
    ...
  AssertionError

An exception is raised in the :keyword:`with` block above, but as you can see
from the print statement in the :keyword:`except` clause :py:meth:`c.__exit__`
(and thereby :py:meth:`c.close`) has been called.

.. important:: Always call :py:meth:`~fiona.collection.Collection.close` or 
   use :keyword:`with` and you'll never stumble over tied-up external resources,
   locked files, etc.

Format Drivers, CRS, Bounds, and Schema
=======================================

In addition to attributes like those of :py:class:`file`
(:py:attr:`~file.name`, :py:attr:`~file.mode`, :py:attr:`~file.closed`),
a :py:class:`~fiona.collection.Collection` has a read-only
:py:attr:`~fiona.collection.Collection.driver` attribute which names the
:program:`OGR` :dfn:`format driver` used to open the vector file.

.. sourcecode:: pycon

  >>> c = fiona.open('docs/data/test_uk.shp', 'r')
  >>> c.driver
  'ESRI Shapefile'

The :dfn:`coordinate reference system` (CRS) of the collection's vector data is
accessed via a read-only :py:attr:`~fiona.collection.Collection.crs` attribute.

.. sourcecode:: pycon

  >>> c.crs
  {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

The CRS is represented by a mapping of :program:`PROJ.4` parameters.

The :py:mod:`fiona.crs` module provides 3 functions to assist with these
mappings. :py:func:`~fiona.crs.to_string` converts mappings to PROJ.4 strings:

.. sourcecode:: pycon

  >>> from fiona.crs import to_string
  >>> print to_string(c.crs)
  +datum=WGS84 +ellps=WGS84 +no_defs +proj=longlat

:py:func:`~fiona.crs.from_string` does the inverse.

.. sourcecode:: pycon

  >>> from fiona.crs import from_string
  >>> from_string("+datum=WGS84 +ellps=WGS84 +no_defs +proj=longlat")
  {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

:py:func:`~fiona.crs.from_epsg` is a shortcut to CRS mappings from EPSG codes.

.. sourcecode:: pycon

  >>> from fiona.crs import from_epsg
  >>> from_epsg(3857)
  {'init': 'epsg:3857', 'no_defs': True}

The number of records in the collection's file can be obtained via Python's
built in :py:func:`len` function.

.. sourcecode:: pycon

  >>> len(c)
  48

The :dfn:`minimum bounding rectangle` (MBR) or :dfn:`bounds` of the
collection's records is obtained via a read-only
:py:attr:`~fiona.collection.Collection.bounds` attribute.

.. sourcecode:: pycon

  >>> c.bounds
  (-8.6213890000000006, 49.911659, 1.749444, 60.844444000000003)

Finally, the schema of its record type (a vector file has a single type of
record, remember) is accessed via a read-only
:py:attr:`~fiona.collection.Collection.schema` attribute.

.. sourcecode:: pycon

  >>> import pprint
  >>> pprint.pprint(c.schema)
  {'geometry': 'Polygon',
   'properties': {'AREA': 'float',
                  'CAT': 'float',
                  'CNTRY_NAME': 'str',
                  'FIPS_CNTRY': 'str',
                  'POP_CNTRY': 'float'}}

Keeping Schemas Simple
----------------------

Fiona takes a less is more approach to record types and schemas. Data about
record types is structured as closely to data about records as can be done.
Modulo a record's 'id' key, the keys of a schema mapping are the same as the
keys of the collection's record mappings.

.. sourcecode:: pycon

  >>> rec = next(c)
  >>> set(rec.keys()) - set(c.schema.keys())
  set(['id'])
  >>> set(rec['properties'].keys()) == set(c.schema['properties'].keys())
  True

The values of the schema mapping are either additional mappings or field type
names like 'Polygon', 'float', and 'str'. The corresponding Python types can
be found in a dictionary named :py:attr:`fiona.types`.

.. sourcecode:: pycon

  >>> pprint.pprint(fiona.types)
  {'date': <class 'fiona.ogrext.FionaDateType'>,
   'datetime': <class 'fiona.ogrext.FionaDateTimeType'>,
   'float': <type 'float'>,
   'int': <type 'int'>,
   'str': <type 'unicode'>,
   'time': <class 'fiona.ogrext.FionaTimeType'>}

Field Types
-----------

In a nutshell, the types and their names are as near to what you'd expect in
Python (or Javascript) as possible. The 'str' vs 'unicode' muddle is a fact of
life in Python < 3.0. Fiona records have Unicode strings, but their field type
name is 'str' (looking forward to Python 3).

.. sourcecode:: pycon

  >>> type(rec['properties']['CNTRY_NAME'])
  <type 'unicode'>
  >>> c.schema['properties']['CNTRY_NAME']
  'str'
  >>> fiona.types[c.schema['properties']['CNTRY_NAME']]
  <type 'unicode'>

String type fields may also indicate their maximum width. A value of 'str:25'
indicates that all values will be no longer than 25 characters. If this value
is used in the schema of a file opened for writing, values of that property
will be truncated at 25 characters. The default width is 80 chars, which means
'str' and 'str:80' are more or less equivalent.

Fiona provides a function to get the width of a property.

.. sourcecode:: pycon

  >>> from fiona import prop_width
  >>> prop_width('str:25')
  25
  >>> prop_width('str')
  80

Another function gets the proper Python type of a property.

.. sourcecode:: pycon

  >>> from fiona import prop_type
  >>> prop_type('int')
  <type 'int'>
  >>> prop_type('float')
  <type 'float'>
  >>> prop_type('str:25')
  <type 'unicode'>

The example above is for Python 2. With Python 3, the type of 'str' properties
is different.

.. sourcecode:: pycon

  >>> prop_type('str:25')
  <class 'str'>

Geometry Types
--------------

Fiona supports the geometry types in GeoJSON and their 3D variants. This means
that the value of a schema's geometry item will be one of the following:

 - Point
 - LineString
 - Polygon
 - MultiPoint
 - MultiLineString
 - MultiPolygon
 - GeometryCollection
 - 3D Point
 - 3D LineString
 - 3D Polygon
 - 3D MultiPoint
 - 3D MultiLineString
 - 3D MultiPolygon
 - 3D GeometryCollection

The last seven of these, the 3D types, apply only to collection schema. The
geometry types of features are always one of the first seven. A '3D Point'
collection, for example, always has features with geometry type 'Point'. The
coordinates of those geometries will be (x, y, z) tuples.

Note that one of the most common vector data formats, Esri's Shapefile, has no
'MultiLineString' or 'MultiPolygon' schema geometries. However, a Shapefile
that indicates 'Polygon' in its schema may yield either 'Polygon' or
'MultiPolygon' features.

Records
=======

A record you get from a collection is a Python :py:class:`dict` structured
exactly like a GeoJSON Feature. Fiona records are self-describing; the names of
its fields are contained within the data structure and the values in the fields
are typed properly for the type of record. Numeric field values are instances
of type :py:class:`int` and :py:class:`float`, for example, not strings.

.. sourcecode:: pycon

  >>> pprint.pprint(rec)
  {'geometry': {'coordinates': [[(-4.6636110000000004, 51.158332999999999),
                                 (-4.669168, 51.159438999999999),
                                 (-4.6733339999999997, 51.161385000000003),
                                 (-4.6744450000000004, 51.165275999999999),
                                 (-4.6713899999999997, 51.185271999999998),
                                 (-4.6694449999999996, 51.193053999999997),
                                 (-4.6655559999999996, 51.195),
                                 (-4.6588900000000004, 51.195),
                                 (-4.6563889999999999, 51.192214999999997),
                                 (-4.6463890000000001, 51.164444000000003),
                                 (-4.6469449999999997, 51.160828000000002),
                                 (-4.6516679999999999, 51.159438999999999),
                                 (-4.6636110000000004, 51.158332999999999)]],
                'type': 'Polygon'},
   'id': '1',
   'properties': {'AREA': 244820.0,
                  'CAT': 232.0,
                  'CNTRY_NAME': u'United Kingdom',
                  'FIPS_CNTRY': u'UK',
                  'POP_CNTRY': 60270708.0}}

The record data has no references to the
:py:class:`~fiona.collection.Collection` from which it originates or to any
other external resource. It's entirely independent and safe to use in any way.
Closing the collection does not affect the record at all.

.. sourcecode:: pycon

  >>> c.close()
  >>> rec['id']
  '1'

Record Id
---------

A record has an ``id`` key. As in the GeoJSON specification, its corresponding
value is a string unique within the data file.

.. sourcecode:: pycon

  >>> c = fiona.open('docs/data/test_uk.shp', 'r')
  >>> rec = next(c)
  >>> rec['id']
  '0'

.. admonition:: OGR Details

   In the :program:`OGR` model, feature ids are long integers. Fiona record ids
   are therefore usually string representations of integer record indexes.

Record Properties
-----------------

A record has a ``properties`` key. Its corresponding value is a mapping. The
keys of the properties mapping are the same as the keys of the properties
mapping in the schema of the collection the record comes from (see above). 

.. sourcecode:: pycon

  >>> pprint.pprint(rec['properties'])
  {'AREA': 244820.0,
   'CAT': 232.0,
   'CNTRY_NAME': u'United Kingdom',
   'FIPS_CNTRY': u'UK',
   'POP_CNTRY': 60270708.0}

Record Geometry
---------------

A record has a ``geometry`` key. Its corresponding value is a mapping with
``type`` and ``coordinates`` keys.

.. sourcecode:: pycon

  >>> pprint.pprint(rec['geometry'])
  {'coordinates': [[(0.89916700000000005, 51.357216000000001),
                    (0.88527800000000001, 51.358330000000002),
                    (0.78749999999999998, 51.369438000000002),
                    (0.781111, 51.370552000000004),
                    (0.76611099999999999, 51.375832000000003),
                    (0.75944400000000001, 51.380828999999999),
                    (0.745278, 51.394440000000003),
                    (0.74083299999999996, 51.400275999999998),
                    (0.73499999999999999, 51.408332999999999),
                    (0.74055599999999999, 51.429718000000001),
                    (0.74888900000000003, 51.443604000000001),
                    (0.76027800000000001, 51.444716999999997),
                    (0.79111100000000001, 51.439995000000003),
                    (0.89222199999999996, 51.421387000000003),
                    (0.90416700000000005, 51.418883999999998),
                    (0.90888899999999995, 51.416938999999999),
                    (0.93055500000000002, 51.398887999999999),
                    (0.93666700000000003, 51.393608),
                    (0.94388899999999998, 51.384995000000004),
                    (0.94750000000000001, 51.378608999999997),
                    (0.94777800000000001, 51.374718000000001),
                    (0.94694400000000001, 51.371108999999997),
                    (0.9425, 51.369163999999998),
                    (0.90472200000000003, 51.358055),
                    (0.89916700000000005, 51.357216000000001)]],
   'type': 'Polygon'}

Since the coordinates are just tuples, or lists of tuples, or lists of lists of
tuples, the ``type`` tells you how to interpret them.

+-------------------+---------------------------------------------------+
| Type              | Coordinates                                       |
+===================+===================================================+
| Point             | A single (x, y) tuple                             |
+-------------------+---------------------------------------------------+
| LineString        | A list of (x, y) tuple vertices                   |
+-------------------+---------------------------------------------------+
| Polygon           | A list of rings (each a list of (x, y) tuples)    |
+-------------------+---------------------------------------------------+
| MultiPoint        | A list of points (each a single (x, y) tuple)     |
+-------------------+---------------------------------------------------+
| MultiLineString   | A list of lines (each a list of (x, y) tuples)    |
+-------------------+---------------------------------------------------+
| MultiPolygon      | A list of polygons (see above)                    |
+-------------------+---------------------------------------------------+

Fiona, like the GeoJSON format, has both Northern Hemisphere "North is up" and
Cartesian "X-Y" biases. The values within a tuple that denoted as ``(x, y)``
above are either (longitude E of the prime meridian, latitude N of the equator)
or, for other projected coordinate systems, (easting, northing).

.. admonition:: Long-Lat, not Lat-Long

   Even though most of us say "lat, long" out loud, Fiona's ``x,y`` is always
   easting, northing, which means ``(long, lat)``. Longitude first and latitude
   second, consistent with the GeoJSON format specification.

Point Set Theory and Simple Features
------------------------------------

In a proper, well-scrubbed vector data file the geometry mappings explained
above are representations of geometric objects made up of :dfn:`point sets`.
The following

.. sourcecode:: python

  {'type': 'LineString', 'coordinates': [(0.0, 0.0), (0.0, 1.0)]}

represents not just two points, but the set of infinitely many points along the
line of length 1.0 from ``(0.0, 0.0)`` to ``(0.0, 1.0)``. In the application of
point set theory commonly called :dfn:`Simple Features Access` [SFA]_ two
geometric objects are equal if their point sets are equal whether they are
equal in the Python sense or not. If you have Shapely (which implements Simple
Features Access) installed, you can see this in by verifying the following.

.. sourcecode:: pycon

  >>> from shapely.geometry import shape
  >>> l1 = shape(
  ...     {'type': 'LineString', 'coordinates': [(0, 0), (2, 2)]})
  >>> l2 = shape(
  ...     {'type': 'LineString', 'coordinates': [(0, 0), (1, 1), (2, 2)]})
  >>> l1 == l2
  False
  >>> l1.equals(l2)
  True

.. admonition:: Dirty data

   Some files may contain vectors that are :dfn:`invalid` from a simple
   features standpoint due to accident (inadequate quality control on the
   producer's end) or intention ("dirty" vectors saved to a file for special
   treatment). Fiona doesn't sniff for or attempt to clean dirty data, so make
   sure you're getting yours from a clean source.

Writing Vector Data
===================

A vector file can be opened for writing in mode ``'a'`` (append) or mode
``'w'`` (write).

.. admonition:: Note
   
   The in situ "update" mode of :program:`OGR` is quite format dependent
   and is therefore not supported by Fiona.

Appending Data to Existing Files
--------------------------------

Let's start with the simplest if not most common use case, adding new records
to an existing file. The file is copied before modification and a suitable
record extracted in the example below.

.. sourcecode:: pycon

  >>> with fiona.open('docs/data/test_uk.shp', 'r') as c:
  ...     rec = next(c)
  >>> rec['id'] = '-1'
  >>> rec['properties']['CNTRY_NAME'] = u'Gondor'
  >>> import os
  >>> os.system("cp docs/data/test_uk.* /tmp")
  0

The coordinate reference system. format, and schema of the file are already
defined, so it's opened with just two arguments as for reading, but in ``'a'``
mode. The new record is written to the end of the file using the
:py:meth:`~fiona.collection.Collection.write` method. Accordingly, the length
of the file grows from 48 to 49.

.. sourcecode:: pycon

  >>> with fiona.open('/tmp/test_uk.shp', 'a') as c:
  ...     print len(c)
  ...     c.write(rec)
  ...     print len(c)
  ... 
  48
  49

The record you write must match the file's schema (because a file contains one
type of record, remember). You'll get a :py:class:`ValueError` if it doesn't.

.. sourcecode:: pycon

  >>> with fiona.open('/tmp/test_uk.shp', 'a') as c:
  ...     c.write({'properties': {'foo': 'bar'}})
  ... 
  Traceback (most recent call last):
    ...
  ValueError: Record data not match collection schema

Now, what about record ids? The id of a record written to a file is ignored and
replaced by the next value appropriate for the file. If you read the file just
appended to above,

.. sourcecode:: pycon

  >>> with fiona.open('/tmp/test_uk.shp', 'a') as c:
  ...     records = list(c)
  >>> records[-1]['id']
  '48'
  >>> records[-1]['properties']['CNTRY_NAME']
  u'Gondor'

You'll see that the id of ``'-1'`` which the record had when written is
replaced by ``'48'``.

The :py:meth:`~fiona.collection.Collection.write` method writes a single
record to the collection's file. Its sibling
:py:meth:`~fiona.collection.Collection.writerecords` writes a sequence (or
iterator) of records.

.. sourcecode:: pycon

  >>> with fiona.open('/tmp/test_uk.shp', 'a') as c:
  ...     c.writerecords([rec, rec, rec])
  ...     print len(c)
  ... 
  52

.. admonition:: Duplication

   Fiona's collections do not guard against duplication. The code above will
   write 3 duplicate records to the file, and they will be given unique
   sequential ids.

.. admonition:: Buffering

   Fiona's output is buffered. The records passed to :py:meth:`write` and
   :py:meth:`writerecords` are flushed to disk when the collection is closed.
   You may also call :py:meth:`flush` periodically to write the buffer contents
   to disk.

Writing New Files
-----------------

Writing a new file is more complex than appending to an existing file because
the file CRS, format, and schema have not yet been defined and must be done so
by the programmer. Still, it's not very complicated. A schema is just
a mapping, as described above. A CRS is also just a mapping, and the possible
formats are enumerated in the :py:attr:`fiona.drivers` list.

Copy the parameters of our demo file.

.. sourcecode:: pycon

  >>> with fiona.open('docs/data/test_uk.shp', 'r') as source:
  ...     source_driver = source.driver
  ...     source_crs = source.crs
  ...     source_schema = source.schema
  ... 
  >>> source_driver
  'ESRI Shapefile'
  >>> source_crs
  {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}
  >>> pprint.pprint(source_schema)
  {'geometry': 'Polygon',
   'properties': {'AREA': 'float',
                  'CAT': 'float',
                  'CNTRY_NAME': 'str',
                  'FIPS_CNTRY': 'str',
                  'POP_CNTRY': 'float'}}

And now create a new file using them.

.. sourcecode:: pycon

  >>> with fiona.open(
  ...         '/tmp/foo.shp',
  ...         'w',
  ...         driver=source_driver,
  ...         crs=source_crs,
  ...         schema=source_schema) as c:
  ...     print len(c)
  ...     c.write(rec)
  ...     print len(c)
  ... 
  0
  1
  >>> c.closed
  True
  >>> len(c)
  1

The :py:attr:`~fiona.collection.Collection.meta` attribute makes duplication of
a file's meta properties even easier.

.. sourcecode:: pycon

  >>> source = fiona.open('docs/data/test_uk.shp', 'r')
  >>> sink = fiona.open('/tmp/foo.shp', 'w', **source.meta)

Coordinates and Geometry Types
------------------------------

If you write 3D coordinates, ones having (x, y, z) tuples, to a 2D file
('Point' schema geometry, for example) the z values will be lost.

If you write 2D coordinates, ones having only (x, y) tuples, to a 3D file ('3D
Point' schema geometry, for example) a default z value of 0 will be provided.


Advanced Topics
===============

Reading Multilayer data
-----------------------

Up to this point, only simple datasets with one thematic layer or feature type
per file have been shown and the venerable Esri Shapefile has been the primary
example. Other GIS data formats can encode multiple layers or feature types
within a single file or directory. Esri's `File Geodatabase
<http://www.gdal.org/ogr/drv_filegdb.html>`__ is one example of such a format.
A more useful example, for the purpose of this manual, is a directory
comprising multiple shapefiles. The following three shell commands will create
just such a two layered data source from the test data distributed with Fiona.

.. sourcecode:: console

  $ mkdir /tmp/data
  $ ogr2ogr /tmp/data/ docs/data/test_uk.shp test_uk -nln foo
  $ ogr2ogr /tmp/data/ docs/data/test_uk.shp test_uk -nln bar

The layers of a data source can be listed using :py:func:`fiona.listlayers`.

.. sourcecode:: pycon

  >>> fiona.listlayers('/tmp/data')
  ['bar', 'foo']

Unlike OGR, Fiona has no classes representing layers or data sources. To access
the features of a layer, open a collection using the path to the data source
and specify the layer by name using the `layer` keyword.

.. sourcecode:: pycon

  >>> import pprint
  >>> datasrc_path = '/tmp/data'
  >>> for name in fiona.listlayers(datasrc_path):
  ...     with fiona.open(datasrc_path, layer=name) as c:
  ...         pprint.pprint(c.schema)
  ...
  {'geometry': 'Polygon',
   'properties': {'AREA': 'float:15.2',
                  'CAT': 'float:16',
                  'CNTRY_NAME': 'str',
                  'FIPS_CNTRY': 'str',
                  'POP_CNTRY': 'float:15.2'}}
  {'geometry': 'Polygon',
   'properties': {'AREA': 'float:15.2',
                  'CAT': 'float:16',
                  'CNTRY_NAME': 'str',
                  'FIPS_CNTRY': 'str',
                  'POP_CNTRY': 'float:15.2'}}

Layers may also be specified by their index.

.. sourcecode:: pycon

  >>> for i, name in enumerate(fiona.listlayers(datasrc_path)):
  ...     with fiona.open(datasrc_path, layer=i) as c:
  ...         print(len(c))
  ...
  48
  48

If no layer is specified, :py:func:`fiona.open` returns an open collection using the
first layer.

.. sourcecode:: pycon

  >>> with fiona.open(datasrc_path) as c:
  ...     c.name == fiona.listlayers(datasrc_path)[0]
  ...
  True

Writing Multilayer data
-----------------------

To write an entirely new layer to a multilayer data source, simply provide
a unique name to the `layer` keyword argument.

.. sourcecode:: pycon

  >>> 'wah' not in fiona.listlayers(datasrc_path)
  True
  >>> with fiona.open(datasrc_path, layer='bar') as c:
  ...     with fiona.open(datasrc_path, 'w', layer='wah', **c.meta) as d:
  ...         d.write(next(c))
  ...
  >>> fiona.listlayers(datasrc_path)
  ['bar', 'foo', 'wah']

In ``'w'`` mode, existing layers will be overwritten if specified, just as normal
files are overwritten by Python's :py:func:`open` function.

.. sourcode:: pycon

  >>> 'wah' in fiona.listlayers(datasrc_path)
  True
  >>> with fiona.open(datasrc_path, layer='bar') as c:
  ...     with fiona.open(datasrc_path, 'w', layer='wah', **c.meta) as d:
  ...         # Overwrites the existing layer named 'wah'!

Virtual filesystems
-------------------

Zip and Tar archives can be treated as virtual filesystems and collections can
be made from paths and layers within them. In other words, Fiona lets you read
zipped Shapefiles. For example, make a Zip archive from the shapefile
distributed with Fiona.

.. sourcecode:: console

  $ zip /tmp/zed.zip docs/data/test_uk.*
  adding: docs/data/test_uk.shp (deflated 48%)
  adding: docs/data/test_uk.shx (deflated 37%)
  adding: docs/data/test_uk.dbf (deflated 98%)
  adding: docs/data/test_uk.prj (deflated 15%)

The `vfs` keyword parameter for :py:func:`fiona.listlayers` and
:py:func:`fiona.open` may be an Apache Commons VFS style string beginning with
"zip://" or "tar://" and followed by an absolute or relative path to the
archive file. When this parameter is used, the first argument to must be an
absolute path within that archive. The layers in that Zip archive are:

.. sourcecode:: pycon

  >>> import fiona
  >>> fiona.listlayers('/docs/data', vfs='zip:///tmp/zed.zip')
  ['test_uk']

The single shapefile may also be accessed like so:

.. sourcecode:: pycon

  >>> with fiona.open(
  ...         '/docs/data/test_uk.shp', 
  ...         vfs='zip:///tmp/zed.zip') as c:
  ...     print(len(c))
  ...
  48

References
==========

.. [Kent1978] William Kent, Data and Reality, North Holland, 1978.
.. [ESRI1998] ESRI Shapefile Technical Description. July 1998. http://www.esri.com/library/whitepapers/pdfs/shapefile.pdf
.. [GeoJSON] http://geojson.org
.. [JSON] http://www.ietf.org/rfc/rfc4627
.. [SFA] http://en.wikipedia.org/wiki/Simple_feature_access

