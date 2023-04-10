=====================
The Fiona User Manual
=====================

:Author: Sean Gillies, <sean.gillies@gmail.com>
:Version: |release|
:Date: |today|
:Copyright:
  This work, with the exception of code examples, is licensed under a `Creative
  Commons Attribution 3.0 United States License`__. The code examples are
  licensed under the BSD 3-clause license (see LICENSE.txt in the repository
  root).

.. __: https://creativecommons.org/licenses/by/3.0/us/

:Abstract:
  Fiona is OGR's neat, nimble, no-nonsense API. This document explains how to
  use the Fiona package for reading and writing geospatial data files. Python
  3 is used in examples. See the `README <README.html>`__ for installation and
  quick start instructions.

.. sectnum::


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
wrapper for vector data access functions from the `GDAL/OGR
<https://gdal.org>`_ library.  A very simple wrapper for minimalists.
It reads data records from files as GeoJSON-like mappings and writes the same
kind of mappings as records back to files. That's it. There are no layers, no
cursors, no geometric operations, no transformations between coordinate
systems, no remote method calls; all these concerns are left to other Python
packages such as :py:mod:`Shapely <https://github.com/shapely/shapely>` and
:py:mod:`pyproj <https://pypi.org/project/pyproj/>` and Python language
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

The first example of using Fiona is this: copying features (another word for
record) from one file to another, adding two attributes and making sure that
all polygons are facing "up". Orientation of polygons is significant in some
applications, extruded polygons in Google Earth for one. No other library (like
:py:mod:`Shapely`) is needed here, which keeps it uncomplicated. There's a
:file:`coutwildrnp.zip` file in the Fiona repository for use in this and other
examples.

.. code-block:: python

    import datetime

    import fiona
    from fiona import Geometry, Feature, Properties


    def signed_area(coords):
        """Return the signed area enclosed by a ring using the linear time
        algorithm at http://www.cgafaq.info/wiki/Polygon_Area. A value >= 0
        indicates a counter-clockwise oriented ring.
        """
        xs, ys = map(list, zip(*coords))
        xs.append(xs[1])
        ys.append(ys[1])
        return sum(xs[i] * (ys[i + 1] - ys[i - 1]) for i in range(1, len(coords))) / 2.0


    with fiona.open(
        "zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip"
    ) as src:

        # Copy the source schema and add two new properties.
        dst_schema = src.schema
        dst_schema["properties"]["signed_area"] = "float"
        dst_schema["properties"]["timestamp"] = "datetime"

        # Create a sink for processed features with the same format and
        # coordinate reference system as the source.
        with fiona.open(
            "example.gpkg",
            mode="w",
            layer="oriented-ccw",
            crs=src.crs,
            driver="GPKG",
            schema=dst_schema,
        ) as dst:
            for feat in src:
                # If any feature's polygon is facing "down" (has rings
                # wound clockwise), its rings will be reordered to flip
                # it "up".
                geom = feat.geometry
                assert geom.type == "Polygon"
                rings = geom.coordinates
                sa = sum(signed_area(ring) for ring in rings)

                if sa < 0.0:
                    rings = [r[::-1] for r in rings]
                    geom = Geometry(type=geom.type, coordinates=rings)

                # Add the signed area of the polygon and a timestamp
                # to the feature properties map.
                props = Properties.from_dict(
                    **feat.properties,
                    signed_area=sa,
                    timestamp=datetime.datetime.now().isoformat()
                )

                dst.write(Feature(geometry=geom, properties=props))

Data Model
==========

Discrete geographic features are usually represented in geographic information
systems by :dfn:`records`. The characteristics of records and their semantic
implications are well known [Kent1978]_. Among those most significant for
geographic data: records have a single type, all records of that type have the
same fields, and a record's fields concern a single geographic feature.
Different systems model records in different ways, but the various models have
enough in common that programmers have been able to create useful abstract data
models.  The `OGR model <https://gdal.org/user/vector_data_model.html>`__ is one. Its
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

.. code-block:: pycon

    >>> import fiona
    >>> colxn = fiona.open("zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip", "r")
    >>> colxn
    <open Collection '/vsizip/vsicurl/https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip:coutwildrnp', mode 'r' at 0x7f9555af8f50>
    >>> collection.closed
    False

Mode ``'r'`` is the default and will be omitted in following examples.

Fiona's :py:class:`~fiona.collection.Collection` is like a Python
:py:class:`file`, but is iterable for records rather than lines.

.. code-block:: pycon

    >>> next(iter(colxn))
    {'geometry': {'type': 'Polygon', 'coordinates': ...
    >>> len(list(colxn))
    67

Note that :py:func:`list` iterates over the entire collection, effectively
emptying it as with a Python :py:class:`file`.

.. code-block:: pycon

    >>> next(iter(colxn))
    Traceback (most recent call last):
    ...
    StopIteration
    >>> len(list(colxn))
    0

Seeking the beginning of the file is not supported. You must reopen the
collection to get back to the beginning.

.. code-block:: pycon

    >>> colxn = fiona.open("zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip")
    >>> len(list(colxn))
    67

.. admonition:: File Encoding

   The format drivers will attempt to detect the encoding of your data, but may
   fail. In my experience GDAL 1.7.2 (for example) doesn't detect that the
   encoding of the Natural Earth dataset is Windows-1252. In this case, the
   proper encoding can be specified explicitly by using the ``encoding``
   keyword parameter of :py:func:`fiona.open`: ``encoding='Windows-1252'``.

   New in version 0.9.1.

Collection indexing
-------------------

Features of a collection may also be accessed by index.

.. code-block:: pycon

    >>> with fiona.open("zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip") as colxn:
    ...     print(colxn[1])
    ...
    <fiona.model.Feature object at 0x7f954bfc5f50>

Note that these indices are controlled by GDAL, and do not always follow Python
conventions. They can start from 0, 1 (e.g. geopackages), or even other values,
and have no guarantee of contiguity. Negative indices will only function
correctly if indices start from 0 and are contiguous.

New in version 1.1.6

Closing Files
-------------

A :py:class:`~fiona.collection.Collection` involves external resources. There's
no guarantee that these will be released unless you explicitly
:py:meth:`~fiona.collection.Collection.close` the object or use
a :keyword:`with` statement. When a :py:class:`~fiona.collection.Collection`
is a context guard, it is closed no matter what happens within the block.

.. code-block:: pycon

    >>> try:
    ...     with fiona.open("zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip") as colxn:
    ...         print(len(list(colxn)))
    ...         assert True is False
    ... except Exception:
    ...     print(colxn.closed)
    ...     raise
    ...
    67
    True
    Traceback (most recent call last):
      ...
    AssertionError

An exception is raised in the :keyword:`with` block above, but as you can see
from the print statement in the :keyword:`except` clause :py:meth:`colxn.__exit__`
(and thereby :py:meth:`colxn.close`) has been called.

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

.. code-block:: pycon

    >>> colxn = fiona.open("zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip")
    >>> colxn.driver
    'ESRI Shapefile'

The :dfn:`coordinate reference system` (CRS) of the collection's vector data is
accessed via a read-only :py:attr:`~fiona.collection.Collection.crs` attribute.

.. code-block:: pycon

    >>> colxn.crs
    CRS.from_epsg(4326)

The :py:mod:`fiona.crs` module provides 3 functions to assist with these
mappings. :py:func:`~fiona.crs.to_string` converts mappings to PROJ.4 strings:

.. code-block:: pycon

    >>> from fiona.crs import to_string
    >>> to_string(colxn.crs)
    'EPSG:4326'

:py:func:`~fiona.crs.from_string` does the inverse.

.. code-block:: pycon

    >>> from fiona.crs import from_string
    >>> from_string("+datum=WGS84 +ellps=WGS84 +no_defs +proj=longlat")
    CRS.from_epsg(4326)

:py:func:`~fiona.crs.from_epsg` is a shortcut to CRS mappings from EPSG codes.

.. code-block:: pycon

    >>> from fiona.crs import from_epsg
    >>> from_epsg(3857)
    CRS.from_epsg(3857)

.. admonition:: No Validation

   Both :py:func:`~fiona.crs.from_epsg` and :py:func:`~fiona.crs.from_string`
   simply restructure data, they do not ensure that the resulting mapping is
   a pre-defined or otherwise valid CRS in any way.

The number of records in the collection's file can be obtained via Python's
built in :py:func:`len` function.

.. code-block:: pycon

    >>> len(colxn)
    67

The :dfn:`minimum bounding rectangle` (MBR) or :dfn:`bounds` of the
collection's records is obtained via a read-only
:py:attr:`~fiona.collection.Collection.bounds` attribute.

.. code-block:: pycon

    >>> colxn.bounds
    (-113.56424713134766, 37.0689811706543, -104.97087097167969, 41.99627685546875)

Finally, the schema of its record type (a vector file has a single type of
record, remember) is accessed via a read-only
:py:attr:`~fiona.collection.Collection.schema` attribute. It has 'geometry'
and 'properties' items. The former is a string and the latter is an ordered
dict with items having the same order as the fields in the data file.

.. code-block:: pycon

      >>> import pprint
    >>> pprint.pprint(colxn.schema)
    {'geometry': 'Polygon',
      'properties': {'AGBUR': 'str:80',
                     'AREA': 'float:24.15',
                     'FEATURE1': 'str:80',
                    'FEATURE2': 'str:80',
                    'NAME': 'str:80',
                      'PERIMETER': 'float:24.15',
                    'STATE': 'str:80',
                    'STATE_FIPS': 'str:80',
                    'URL': 'str:101',
                    'WILDRNP020': 'int:10'}}

Keeping Schemas Simple
----------------------

Fiona takes a less is more approach to record types and schemas. Data about
record types is structured as closely to data about records as can be done.
Modulo a record's 'id' key, the keys of a schema mapping are the same as the
keys of the collection's record mappings.

.. code-block:: pycon

      >>> feat = next(iter(colxn))
      >>> set(feat.keys()) - set(colxn.schema.keys())
      {'id'}
      >>> set(feat['properties'].keys()) == set(colxn.schema['properties'].keys())
      True

The values of the schema mapping are either additional mappings or field type
names like 'Polygon', 'float', and 'str'. The corresponding Python types can
be found in a dictionary named :py:attr:`fiona.FIELD_TYPES_MAP`.

.. code-block:: pycon

      >>> pprint.pprint(fiona.FIELD_TYPES_MAP)
      {'List[str]': typing.List[str],
        'bytes': <class 'bytes'>,
        'date': <class 'fiona.rfc3339.FionaDateType'>,
     'datetime': <class 'fiona.rfc3339.FionaDateTimeType'>,
     'float': <class 'float'>,
     'int': <class 'int'>,
     'int32': <class 'int'>,
     'int64': <class 'int'>,
     'str': <class 'str'>,
     'time': <class 'fiona.rfc3339.FionaTimeType'>}

Field Types
-----------

In a nutshell, the types and their names are as near to what you'd expect in
Python (or Javascript) as possible. Since Python 3, the 'str' field type
may contain Unicode characters.

.. code-block:: pycon

  >>> type(feat.properties['NAME'])
  <class 'str'>
  >>> colxn.schema['properties']['NAME']
  'str'
  >>> fiona.FIELD_TYPES_MAP[colxn.schema['properties']['NAME']]
  <class 'str'>

String type fields may also indicate their maximum width. A value of 'str:25'
indicates that all values will be no longer than 25 characters. If this value
is used in the schema of a file opened for writing, values of that property
will be truncated at 25 characters. The default width is 80 chars, which means
'str' and 'str:80' are more or less equivalent.

Fiona provides a function to get the width of a property.

.. code-block:: pycon

  >>> from fiona import prop_width
  >>> prop_width('str:25')
  25
  >>> prop_width('str')
  80

Another function gets the proper Python type of a property.

.. code-block:: pycon

  >>> from fiona import prop_type
  >>> prop_type('int')
  <type 'int'>
  >>> prop_type('float')
  <type 'float'>
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

Features
========

A record you get from a collection is structured like a GeoJSON Feature. Fiona
records are self-describing; the names of its fields are contained within the
data structure and the values in the fields are typed properly for the type of
record. Numeric field values are instances of type :py:class:`int` and
:py:class:`float`, for example, not strings.

The record data has no references to the
:py:class:`~fiona.collection.Collection` from which it originates or to any
other external resource. It's entirely independent and safe to use in any way.
Closing the collection does not affect the record at all.

.. admonition:: Features are mappings, not dicts

   In Fiona versions before 1.9.0 features were Python dicts, mutable and JSON
   serializable. Since 1.9.0 features are mappings and not immediately JSON
   serializable.

   Instances of Feature can be converted to dicts with
   :py:func:`fiona.model.to_dict` or serialized using the json module and
   :py:class:`fiona.model.ObjectEncoder`.

Feature Id
----------

A feature has an ``id`` attribute. As in the GeoJSON specification, its
corresponding value is a string unique within the data file.

.. code-block:: pycon

    >>> colxn = fiona.open("zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip")
    >>> feat = next(iter(colxn))
    >>> feat.id
    '0'

.. admonition:: OGR Details

   In the :program:`OGR` model, feature ids are long integers. Fiona record ids
   are therefore usually string representations of integer record indexes.

Feature Properties
------------------

A feature has a ``properties`` attribute. Its value is a mapping.  The keys of
the properties mapping are the same as the keys of the properties mapping in
the schema of the collection the record comes from (see above).

.. code-block:: pycon

    >>> for k, v in feat.properties.items():
    ...     print(k, v)
    ...
    PERIMETER 1.22107
    FEATURE2 None
    NAME Mount Naomi Wilderness
    FEATURE1 Wilderness
    URL http://www.wilderness.net/index.cfm?fuse=NWPS&sec=wildView&wname=Mount%20Naomi
    AGBUR FS
    AREA 0.0179264
    STATE_FIPS 49
    WILDRNP020 332
    STATE UT

Feature Geometry
----------------

A feature has a ``geometry`` attribute. Its value is a mapping with ``type``
and ``coordinates`` keys.

.. code-block:: pycon

    >>> feat.geometry["type"]
    'Polygon'
    >>> feat.geometry["coordinates"]
    [[(-111.73527526855469, 41.995094299316406), ..., (-111.73527526855469, 41.995094299316406)]]

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

.. code-block:: python

  {"type": "LineString", "coordinates": [(0.0, 0.0), (0.0, 1.0)]}

represents not just two points, but the set of infinitely many points along the
line of length 1.0 from ``(0.0, 0.0)`` to ``(0.0, 1.0)``. In the application of
point set theory commonly called :dfn:`Simple Features Access` [SFA]_ two
geometric objects are equal if their point sets are equal whether they are
equal in the Python sense or not. If you have Shapely (which implements Simple
Features Access) installed, you can see this in by verifying the following.

.. code-block:: pycon

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
   producer's end), intention ("dirty" vectors saved to a file for special
   treatment) or discrepancies of the numeric precision models (Fiona can't
   handle fixed precision models yet). Fiona doesn't sniff for or attempt to
   clean dirty data, so make sure you're getting yours from a clean source.

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
to an existing file.

.. code-block:: console

    $ wget https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip
    $ unzip coutwildrnp.zip

The coordinate reference system. format, and schema of the file are already
defined, so it's opened with just two arguments as for reading, but in ``'a'``
mode. The new record is written to the end of the file using the
:py:meth:`~fiona.collection.Collection.write` method. Accordingly, the length
of the file grows from 67 to 68.

.. code-block:: pycon

    >>> with fiona.open("coutwildrnp.shp", "a") as dst:
    ...     print(len(dst))
    ...     with fiona.open("zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip") as src:
    ...         feat = src[0]
    ...         print(feat.id, feat.properties["NAME"])
    ...         dst.write(feat)
    ...     print(len(c))
    ...
    67
    ('0', 'Mount Naomi Wilderness')
    68

The feature you write must match the file's schema (because a file contains one
type of record, remember). You'll get a :py:class:`ValueError` if it doesn't.

.. code-block:: pycon

    >>> with fiona.open("coutwildrnp.shp", "a") as dst:
    ...     dst.write({'properties': {'foo': 'bar'}})
    ...
    Traceback (most recent call last):
      ...
    ValueError: Record data not match collection schema

Now, what about record ids? The id of a record written to a file is ignored and
replaced by the next value appropriate for the file. If you read the file just
appended to above,

.. code-block:: pycon

    >>> with fiona.open("coutwildrnp.shp") as colxn:
    ...     feat = colxn[-1]
    ...
    >>> feat.id
    '67'
    >>> feat.properties["NAME"]
    'Mount Naomi Wilderness'

You'll see that the id of ``'0'`` which the record had when written is replaced
by ``'67'``.

The :py:meth:`~fiona.collection.Collection.write` method writes a single
record to the collection's file. Its sibling
:py:meth:`~fiona.collection.Collection.writerecords` writes a sequence (or
iterator) of records.

.. code-block:: pycon

    >>> with fiona.open("coutwildrnp.shp", "a") as colxn:
    ...     colxn.writerecords([feat, feat, feat])
    ...     print(len(colxn))
    ...
    71

.. admonition:: Duplication

   Fiona's collections do not guard against duplication. The code above will
   write 3 duplicate records to the file, and they will be given unique
   sequential ids.

.. admonition:: Transactions

   Fiona uses transactions during write operations to ensure data integrity.
   :py:meth:`writerecords` will start and commit one transaction. If there
   are lots of records, intermediate commits will be performed at reasonable
   intervals.

   Depending on the driver, a transaction can be a very costly operation.
   Since :py:meth:`write` is just a thin convenience wrapper that calls
   :py:meth:`writerecords` with a single record, you may experience significant
   performance issue if you write lots of features one by one using this method.
   Consider preparing your data first and then writing it in a single call to
   :py:meth:`writerecords`.

.. admonition:: Buffering

   Fiona's output is buffered. The records passed to :py:meth:`write` and
   :py:meth:`writerecords` are flushed to disk when the collection is closed.
   You may also call :py:meth:`flush` periodically to write the buffer contents
   to disk.

.. admonition:: Format requirements

   Format drivers may have specific requirements about what they store. For
   example, the Shapefile driver may "fix" topologically invalid features.

Creating files of the same structure
------------------------------------

Writing a new file is more complex than appending to an existing file because
the file CRS, format, and schema have not yet been defined and must be done so
by the programmer. Still, it's not very complicated. A schema is just
a mapping, as described above. The possible
formats are enumerated in the :py:attr:`fiona.supported_drivers` dictionary.

Review the parameters of our demo file.

.. code-block:: pycon

    >>> with fiona.open(
    ...     "zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip"
    ) as src:
    ...     driver = src.driver
    ...     crs = src.crs
    ...     schema = src.schema
    ...     feat = src[1]
    ...
    >>> driver
    'ESRI Shapefile'
    >>> crs
    CRS.from_epsg(4326)
    >>> pprint.pprint(schema)
    {'geometry': 'Polygon',
     'properties': {'AGBUR': 'str:80',
                    'AREA': 'float:24.15',
                    'FEATURE1': 'str:80',
                    'FEATURE2': 'str:80',
                    'NAME': 'str:80',
                    'PERIMETER': 'float:24.15',
                    'STATE': 'str:80',
                    'STATE_FIPS': 'str:80',
                    'URL': 'str:101',
                    'WILDRNP020': 'int:10'}}

We can create a new file using them.

.. code-block:: pycon

    >>> with fiona.open("example.shp", "w", driver=driver, crs=crs, schema=schema) as dst:
    ...     print(len(dst))
    ...     dst.write(feat)
    ...     print(len(dst))
    ...
    0
    1
    >>> dst.closed
    True
    >>> len(dst)
    1

Because the properties of the source schema are ordered and are passed in the
same order to the write-mode collection, the written file's fields have the
same order as those of the source file.

The :py:attr:`~fiona.collection.Collection.profile` attribute makes duplication of
a file's meta properties even easier.

.. code-block:: pycon

    >>> src = fiona.open("zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip")
    >>> dst = fiona.open("example.shp", "w", **src.profile)

Writing new files from scratch
-------------------------------

To write a new file from scratch we have to define our own specific driver, crs
and schema.

To ensure the order of the attribute fields is predictable, in both the schema
and the actual manifestation as feature attributes, we will use ordered
dictionaries.

.. code-block:: pycon

Consider the following record, structured in accordance to the `Python geo
protocol <https://gist.github.com/sgillies/2217756>`__, representing the Eiffel
Tower using a point geometry with UTM coordinates in zone 31N.

.. code-block:: pycon

    >>> eiffel_tower =  {
    ...   'geometry': {
    ...     'type': 'Point',
    ...     'coordinates': (448252, 5411935)
    ...   },
    ...   'properties': dict([
    ...     ('name', 'Eiffel Tower'),
    ...     ('height', 300.01),
    ...     ('view', 'scenic'),
    ...     ('year', 1889)
    ...   ])
    ... }

A corresponding scheme could be:

.. code-block:: pycon

    >>> landmarks_schema = {
    ...   'geometry': 'Point',
    ...   'properties': dict([
    ...     ('name', 'str'),
    ...     ('height', 'float'),
    ...     ('view', 'str'),
    ...     ('year', 'int')
    ...   ])
    ... }

The coordinate reference system of these landmark coordinates is ETRS89 / UTM
zone 31N which is referenced in the EPSG database as EPSG:25831.

.. code-block:: pycon

    >>> from fiona.crs import CRS
    >>> landmarks_crs = CRS.from_epsg(25831)

An appropriate driver could be:

.. code-block:: pycon

    >>> driver = "GeoJSON"

Having specified schema, crs and driver, we are ready to open a file for
writing our record:

.. code-block:: pycon

    >>> with fiona.open(
    ...     "landmarks.geojson",
    ...     "w",
    ...     driver="GeoJSON",
    ...     crs=CRS.from_epsg(25831),
    ...     schema=landmarks_schema
    ... ) as colxn:
    ...     colxn.write(eiffel_tower)
    ...

Ordering Record Fields
......................

Beginning with Fiona 1.0.1, the 'properties' item of :py:func:`fiona.open`'s
'schema' keyword argument may be an ordered dict or a list of (key, value)
pairs, specifying an ordering that carries into written files. If an ordinary
dict is given, the ordering is determined by the output of that dict's
:py:func:`~items` method.

3D Coordinates and Geometry Types
---------------------------------

If you write 3D coordinates, ones having (x, y, z) tuples, to a 2D file
('Point' schema geometry, for example) the z values will be lost.

.. code-block:: python

    >>> feat = {"geometry": {"type": "Point", "coordinates": (-1, 1, 5)}}
    >>> with fiona.open(
    ...     "example.shp",
    ...     "w",
    ...     driver="Shapefile",
    ...     schema={"geometry": "Point", "properties": {}}
    ... ) as dst:
    ...     dst.write(feat)
    ...
    >>> with fiona.open("example.shp") as src:
    ...     print(src[0].geometry.coordinates)
    ...
    (-1.0, 1.0)

If you write 2D coordinates, ones having only (x, y) tuples, to a 3D file ('3D
Point' schema geometry, for example) a default z value of 0 will be provided.

.. code-block:: python

    >>> feat = {"geometry": {"type": "Point", "coordinates": (-1, 1)}}
    >>> with fiona.open(
    ...     "example.shp",
    ...     "w",
    ...     driver="Shapefile",
    ...     schema={"geometry": "3D Point", "properties": {}}
    ... ) as dst:
    ...     dst.write(feat)
    ...
    >>> with fiona.open("example.shp") as src:
    ...     print(src[0].geometry.coordinates)
    ...
    (-1.0, 1.0, 0.0)

Advanced Topics
===============

OGR configuration options
-------------------------

GDAL/OGR has a large number of features that are controlled by global or
thread-local `configuration options. <https://gdal.org/user/configoptions.html>`_
Fiona allows you to configure these options using a context manager, ``fiona.Env``.
This class's constructor takes GDAL/OGR configuration options as keyword arguments.
To see debugging information from GDAL/OGR, for example, you may do the following.

.. code-block:: python

    import logging
    import fiona

    logging.basicConfig(level=logging.DEBUG)

    with fiona.Env(CPL_DEBUG=True):
        fiona.open(
            "zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip"
        )

The following extra messages will appear in the Python logger's output.

.. code-block::

    DEBUG:fiona._env:CPLE_None in GNM: GNMRegisterAllInternal
    DEBUG:fiona._env:CPLE_None in GNM: RegisterGNMFile
    DEBUG:fiona._env:CPLE_None in GNM: RegisterGNMdatabase
    DEBUG:fiona._env:CPLE_None in GNM: GNMRegisterAllInternal
    DEBUG:fiona._env:CPLE_None in GNM: RegisterGNMFile
    DEBUG:fiona._env:CPLE_None in GNM: RegisterGNMdatabase
    DEBUG:fiona._env:CPLE_None in GDAL: GDALOpen(tests/data/coutwildrnp.shp, this=0x1683930) succeeds as ESRI Shapefile.

If you call ``fiona.open()`` with no surrounding ``Env`` environment, one will
be created for you.

When your program exits the environment's ``with`` block the configuration reverts
to its previous state.

Driver configuration options
----------------------------

Drivers can have dataset open, dataset creation, respectively layer creation
options. These options can be found on the drivers page on `GDAL's homepage.
<https://gdal.org/drivers/vector/index.html>`_ or using the ``fiona.meta``
module:

.. code-block:: pycon

    >>> import fiona.meta
    >>> fiona.meta.print_driver_options("GeoJSON")

These options can be passed to ``fiona.open``:

.. code-block:: python

    import fiona
    fiona.open('tests/data/coutwildrnp.json', ARRAY_AS_STRING="YES")

Cloud storage credentials
-------------------------

One of the most important uses of ``fiona.Env`` is to set credentials for
accessing data stored in AWS S3 or another cloud storage system.

.. code-block:: python

    import fiona
    from fiona.session import AWSSession

    with fiona.Env(
        session=AWSSession(
            aws_access_key_id="key",
            aws_secret_access_key="secret"
        )
    ):
        fiona.open("zip+s3://example-bucket/example.zip")

The AWSSession class is currently the only credential session manager in Fiona.
The source code has an example of how classes for other cloud storage providers
may be implemented.  AWSSession relies upon boto3 and botocore, which will be
installed as extra dependencies of Fiona if you run ``pip install fiona[s3]``.

If you call ``fiona.open()`` with no surrounding ``Env`` and pass a path to an
S3 object, a session will be created for you using code equivalent to the
following code.

.. code-block:: python

    import boto3

    from fiona.session import AWSSession
    import fiona

    with fiona.Env(session=AWSSession(boto3.Session())):
        fiona.open("zip+s3://fiona-testing/coutwildrnp.zip")

Slicing and masking iterators
-----------------------------

With some vector data formats a spatial index accompanies the data file,
allowing efficient bounding box searches. A collection's
:py:meth:`~fiona.collection.Collection.items` method returns an iterator over
pairs of FIDs and records that intersect a given ``(minx, miny, maxx, maxy)``
bounding box or geometry object. Spatial filtering may be inaccurate and
returning all features overlapping the envelope of the geometry. The
collection's own coordinate reference system (see below) is used to interpret
the box's values. If you want a list of the iterator's items, pass it to
Python's builtin :py:func:`list` as shown below.

.. code-block:: pycon

    >>> colxn = fiona.open(
    ...     "zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip"
    ... )
    >>> hits = list(colxn.items(bbox=(-110.0, 36.0, -108.0, 38.0)))
    >>> len(hits)
    5

The iterator method takes the same ``stop`` or ``start, stop[, step]``
slicing arguments as :py:func:`itertools.islice`.
To get just the first two items from that iterator, pass a stop index.

.. code-block:: pycon

    >>> hits = colxn.items(2, bbox=(-110.0, 36.0, -108.0, 38.0)))
    >>> len(list(hits))
    2

To get the third through fifth items from that iterator, pass start and stop
indexes.

.. code-block:: pycon

    >>> hits = colxn.items(2, 5, bbox=(-110.0, 36.0, -108.0, 38.0)))
    >>> len(list(hits))
    3

To filter features by property values, use Python's builtin :py:func:`filter` and
:keyword:`lambda` or your own filter function that takes a single feature
record and returns ``True`` or ``False``.

.. code-block:: pycon

    >>> def pass_positive_area(rec):
    ...     return rec['properties'].get('AREA', 0.0) > 0.0
    ...
    >>> colxn = fiona.open(
    ...     "zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip"
    ... )
    >>> hits = filter(pass_positive_area, colxn)
    >>> len(list(hits))
    67

Reading Multilayer data
-----------------------

Up to this point, only simple datasets with one thematic layer or feature type
per file have been shown and the venerable Esri Shapefile has been the primary
example. Other GIS data formats can encode multiple layers or feature types
within a single file or directory. GeoPackage is one example of such a format.
A more useful example, for the purpose of this manual, is a directory or
zipfile comprising multiple shapefiles. The GitHub-hosted zipfile we've been
using in these examples is, in fact, such a multilayer dataset.

The layers of a dataset can be listed using :py:func:`fiona.listlayers`. In
the shapefile format case, layer names match base names of the files.

.. code-block:: pycon

    >>> fiona.listlayers(
    ...     "zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip"
    ... )
    ['coutwildrnp']

Unlike OGR, Fiona has no classes representing layers or data sources. To access
the features of a layer, open a collection using the path to the data source
and specify the layer by name using the `layer` keyword.

.. code-block:: pycon

    dataset_path = "zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip"
    >>> for name in fiona.listlayers(dataset_path):
    ...     with fiona.open(dataset_path, layer=name) as colxn:
    ...         pprint.pprint(colxn.schema)
    ...
    {'geometry': 'Polygon',
     'properties': {'AGBUR': 'str:80',
                    'AREA': 'float:24.15',
                    'FEATURE1': 'str:80',
                    'FEATURE2': 'str:80',
                    'NAME': 'str:80',
                    'PERIMETER': 'float:24.15',
                    'STATE': 'str:80',
                    'STATE_FIPS': 'str:80',
                    'URL': 'str:101',
                    'WILDRNP020': 'int:10'}}

Layers may also be specified by their numerical index.

.. code-block:: pycon

    >>> for index, name in enumerate(fiona.listlayers(dataset_path)):
    ...     with fiona.open(dataset_path, layer=index) as colxn:
    ...         print(len(colxn))
    ...
    67

If no layer is specified, :py:func:`fiona.open` returns an open collection
using the first layer.

.. code-block:: pycon

    >>> with fiona.open(dataset_path) as colxn:
    ...     colxn.name == fiona.listlayers(datasset_path)[0]
    ...
    True

We've been relying on this implicit behavior throughout the manual.

The most general way to open a shapefile for reading, using all of the
parameters of :py:func:`fiona.open`, is to treat it as a data source with
a named layer.

.. code-block:: pycon

    >>> fiona.open(
    ...     "zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip",
    ...     mode="r",
    ...     layer="coutwildrnp"
    ... )

In practice, it is fine to rely on the implicit first layer and default ``'r'``
mode and open a shapefile like this:

.. code-block:: pycon

    >>> fiona.open(
    ...     "zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip",
    ... )

Writing Multilayer data
-----------------------

To write an entirely new layer to a multilayer data source, simply provide
a unique name to the `layer` keyword argument.

.. code-block:: pycon

    >>> with fiona.open(
    ...     "zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip",
    ... ) as src:
    ...     with fiona.open("example.gpkg", "w", layer="example one", **src.profile) as dst:
    ...         dst.writerecords(src)
    ...
    >>> fiona.listlayers("example.gpkg")
    ['example one']

In ``'w'`` mode, existing layers will be overwritten if specified, just as normal
files are overwritten by Python's :py:func:`open` function.

Unsupported drivers
-------------------

Fiona maintains a list of OGR drivers in :py:attr:`fiona.supported_drivers`
that are tested and known to work together with Fiona. Opening a dataset using
an unsupported driver or access mode results in an :py:attr: `DriverError`
exception. By passing `allow_unsupported_drivers=True` to :py:attr:`fiona.open`
no compatibility checks are performed and unsupported OGR drivers can be used.
However, there are no guarantees that Fiona will be able to access or write
data correctly using an unsupported driver.

.. code-block:: python

  import fiona

  with fiona.open("file.kmz", allow_unsupported_drivers=True) as collection:
    ...

Not all OGR drivers are necessarily enabled in every GDAL distribution. The
following code snippet lists the drivers included in the GDAL installation
used by Fiona:

.. code-block:: python

  from fiona.env import Env

  with Env() as gdalenv:
      print(gdalenv.drivers().keys())

MemoryFile and ZipMemoryFile
----------------------------

:py:class:`fiona.io.MemoryFile` and :py:class:`fiona.io.ZipMemoryFile` allow
formatted feature collections, even zipped feature collections, to be read or
written in memory, with no filesystem access required. For example, you may
have a zipped shapefile in a stream of bytes coming from a web upload or
download.

.. code-block:: pycon

    >>> data = open('tests/data/coutwildrnp.zip', 'rb').read()
    >>> len(data)
    154006
    >>> data[:20]
    b'PK\x03\x04\x14\x00\x00\x00\x00\x00\xaa~VM\xech\xae\x1e\xec\xab'

The feature collection in this stream of bytes can be accessed by wrapping it
in an instance of ZipMemoryFile.

.. code-block:: pycon

    >>> from fiona.io import ZipMemoryFile
    >>> with ZipMemoryFile(data) as zip:
    ...     with zip.open('coutwildrnp.shp') as collection:
    ...         print(len(collection))
    ...         print(collection.schema)
    ...
    67
    {'properties': OrderedDict([('PERIMETER', 'float:24.15'), ('FEATURE2', 'str:80'), ('NAME', 'str:80'), ('FEATURE1', 'str:80'), ('URL', 'str:101'), ('AGBUR', 'str:80'), ('AREA', 'float:24.15'), ('STATE_FIPS', 'str:80'), ('WILDRNP020', 'int:10'), ('STATE', 'str:80')]), 'geometry': 'Polygon'}

*New in 1.8.0*

Fiona command line interface
============================

Fiona comes with a command line interface called "fio". See the
`CLI Documentation <cli.html>`__ for detailed usage instructions.

Final Notes
===========

This manual is a work in progress and will grow and improve with Fiona.
Questions and suggestions are very welcome. Please feel free to use the `issue
tracker <https://github.com/Toblerity/Fiona/issues>`__ or email the author
directly.

Do see the `README <README.html>`__ for installation instructions and
information about supported versions of Python and other software dependencies.

Fiona would not be possible without the `contributions of other developers
<README.html#credits>`__, especially Frank Warmerdam and Even Rouault, the
developers of GDAL/OGR; and Mike Weisman, who saved Fiona from neglect and
obscurity.

References
==========

.. [Kent1978] William Kent, Data and Reality, North Holland, 1978.
.. [ESRI1998] ESRI Shapefile Technical Description. July 1998. https://www.esri.com/library/whitepapers/pdfs/shapefile.pdf
.. [GeoJSON] https://geojson.org
.. [JSON] https://www.ietf.org/rfc/rfc4627
.. [SFA] https://en.wikipedia.org/wiki/Simple_feature_access
