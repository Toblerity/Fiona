=====================
The Fiona User Manual
=====================

:Author: Sean Gillies, <sean.gillies@gmail.com>
:Revision: 1.0
:Date: 18 February 2012
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
:dfn:`rasters` representing continuous scalar fields (land surface temperature or
elevation, for example) and :dfn:`vectors` representing discrete entities like
roads and administrative boundaries. Concerned exclusively with the latter,
Fiona is a Python wrapper for vector data access functions from the `OGR
<http://www.gdal.org/ogr/>`_ library.  A very simple wrapper for minimalists.
It reads data records from files as GeoJSON-like mappings and writes the same
kind of mappings as records back to files. That's it. There are no layers, no
cursors, no geometric operations, no transformations between coordinate
systems, no remote method calls; all these concerns are left to other Python
packages such as :py:mod:`Shapely <https://github.com/Toblerity/Shapely>` and
:py:mod:`pyproj <http://code.google.com/p/pyproj/>` and Python language
protocols. Why? To eliminate unnecessary complication. Fiona is simple to
understand and use, with no gotchas.

Please understand this: Fiona is designed to excel in a certain range of tasks
and is less optimal in others. Fiona trades memory and speed for simplicity and
reliability. Where OGR's Python bindings (for example) use C pointers, Fiona
copies vector data from the data source to Python objects.  These are simpler
and safer to use, but more memory intensive. Fiona's performance is relatively
more slow if you only need access to a single record field – and of course
if you just want to reproject or filter data files, nothing beats the
:command:`ogr2ogr` program – but Fiona's performance is much better than OGR's
Python bindings if you want *all* fields and coordinates of a record. The
copying is a constraint, yes, but it simplifies things.  With Fiona, you don't
have to track references to C objects to avoid crashes, and you can work with
vector data using familiar Python mapping accessors.  Less worry, less time
spent reading API documentation.

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
  :py:mod:`GeoDjango` in this already. If so, carry on.
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
the Fiona repository that we'll use in this and other examples.

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

Reading a GIS vector file begins by opening it in mode ``"r"`` using Fiona's
:py:func:`~fiona.collection` function. It returns an opened
:py:class:`~fiona.collection.Collection` object.

.. sourcecode:: pycon

  >>> from fiona import collection
  >>> c = collection("docs/data/test_uk.shp", "r")
  >>> c.closed
  False

Fiona's :py:class:`~fiona.collection.Collection` is like a Python
:py:class:`file`, but is iterable for records rather than lines.

.. sourcecode:: pycon

  >>> c.next()
  {'geometry': {'type': 'Polygon', 'coordinates': ...
  >>> len(list(c))
  47

Note that :py:func:`list` iterates over the entire collection, effectively
emptying it as with a Python :py:class:`file`.

.. sourcecode:: pycon

  >>> c.next()
  Traceback (most recent call last):
  ...
  StopIteration
  >>> len(list(c))
  0

A future version of Fiona may (should?) allow you to seek records by their
index, but for now you must reopen the collection to get back to the beginning.

.. sourcecode:: pycon

  >>> c = collection("docs/data/test_uk.shp", "r")
  >>> len(list(c))
  48

Filtering
---------

Details TODO.

.. sourcecode:: pycon

  >>> c = collection("docs/data/test_uk.shp", "r")
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
  ...     with collection("docs/data/test_uk.shp", "r") as c:
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
(:py:attr:`~file.mode`, :py:attr:`~file.closed`),
a :py:class:`~fiona.collection.Collection` has a read-only
:py:attr:`~fiona.collection.Collection.driver` attribute which names the
:program:`OGR` :dfn:`format driver` used to open the vector file.

.. sourcecode:: pycon

  >>> c = collection("docs/data/test_uk.shp", "r")
  >>> c.driver
  'ESRI Shapefile'

The :dfn:`coordinate reference system` (CRS) of the collection's vector data is
accessed via a read-only :py:attr:`~fiona.collection.Collection.crs` attribute.

.. sourcecode:: pycon

  >>> c.crs
  {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

The CRS is represented by a mapping of :program:`PROJ.4` parameters.

The number of records in the collection's file can be obtained via Python's built
in :py:func:`len` function.

.. sourcecode:: pycon

  >>> len(c)
  48

The :dfn:`minimum bounding rectangle` (MBR) or :dfn:`bounds` of the collection's
records is obtained via a read-only
:py:attr:`~fiona.collection.Collection.bounds` attribute.

.. sourcecode:: pycon

  >>> c.bounds
  (-8.6213890000000006, 49.911659, 1.749444, 60.844444000000003)

.. admonition:: Note

   Getting the length or bounds of a collection (or closing a collection) has
   the side effect of flushing any written records to the file on disk. You
   may also call :py:meth:`~fiona.collection.Collection.flush` in your code.
   It does nothing when there are no written records.

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

  >>> rec = c.next()
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

TODO: details. In a nutshell, the types and their names are as near to what you'd
expect in Python (or Javascript) as possible. The 'str' vs 'unicode' muddle is
a fact of life in Python < 3.0. Fiona records have Unicode strings, but their
field type name is 'str'.

.. sourcecode:: pycon

  >>> type(rec['properties']['CNTRY_NAME'])
  <type 'unicode'>
  >>> c.schema['properties']['CNTRY_NAME']
  'str'
  >>> fiona.types[c.schema['properties']['CNTRY_NAME']]
  <type 'unicode'>

Records
=======

A record you get from a collection is a Python :py:class:`dict` structured
exactly like a GeoJSON Feature. Fiona records are self-describing; the names of
its fields are contained within the data structure and the values in the fields
are typed properly for the type of record. Numeric field values are instances of
type :py:class:`int` and :py:class:`float`, for example, not strings.

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
  >>> pprint.pprint(rec['properties'])
  {'AREA': 244820.0,
   'CAT': 232.0,
   'CNTRY_NAME': u'United Kingdom',
   'FIPS_CNTRY': u'UK',
   'POP_CNTRY': 60270708.0}

Record Id
---------

TODO.

Record Properties
-----------------

TODO.

Record Geometry
---------------

TODO.

Writing Vector Data
===================

A vector file can be opened for writing in mode ``"a"`` (append) or mode
``"w"`` (write).

.. admonition:: Note
   
   The in situ "update" mode of :program:`OGR` is quite format dependent
   and is therefore not supported by Fiona.

Appending Data to Existing Files
--------------------------------

Details TODO. 

.. sourcecode:: pycon

  >>> import os
  >>> os.system("cp docs/data/test_uk.* /tmp")
  0
  >>> with collection("/tmp/test_uk.shp", "a") as c:
  ...     print len(c)
  ...     c.write(rec)
  ...     print len(c)
  ... 
  48
  49

The count of records remains even after the collection is closed.

.. sourcecode:: pycon

  >>> c.closed
  True
  >>> len(c)
  49
  

The record you write must match the file's schema (because a file contains one
type of record, remember). You'll get a :py:class:`ValueError` if it doesn't.

.. sourcecode:: pycon

  >>> with collection("/tmp/test_uk.shp", "a") as c:
  ...     c.write({'properties': {'foo': 'bar'}})
  ... 
  Traceback (most recent call last):
    ...
  ValueError: Record data not match collection schema


The :py:meth:`~fiona.collection.Collection.write` method writes a single
record to the collection's file. Its sibling
:py:meth:`~fiona.collection.Collection.writerecords` writes a sequence (or
iterator) of records.

.. sourcecode:: pycon

  >>> with collection("/tmp/test_uk.shp", "a") as c:
  ...     c.writerecords([rec, rec, rec])
  ...     print len(c)
  ... 
  52

.. admonition:: Buffering

   Fiona's output is buffered. The records passed to :py:meth:`write` and 
   :py:meth:`writerecords` are flushed to disk when the collection is closed.
   This means that writing large files is memory intensive. Work is planned to
   make output more efficient by the 1.0 release.

Writing New Files
-----------------

Details TODO.

Copy the parameters of our demo file.

.. sourcecode:: pycon

  >>> with collection("docs/data/test_uk.shp", "r") as source:
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

  >>> with collection(
  ...         "/tmp/foo.shp",
  ...         "w",
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


.. [Kent1978] William Kent, Data and Reality, North Holland, 1978.
.. [ESRI1998] ESRI Shapefile Technical Description. July 1998. http://www.esri.com/library/whitepapers/pdfs/shapefile.pdf
.. [GeoJSON] http://geojson.org
.. [JSON] http://www.ietf.org/rfc/rfc4627

