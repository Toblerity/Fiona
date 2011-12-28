=====================
The Fiona User Manual
=====================

:Author: Sean Gillies, <sean.gillies@gmail.com>
:Revision: 1.0
:Date: 26 December 2011
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

Fiona is nothing more than a simple wrapper for the OGR vector data access
library. A very simple wrapper for minimalists. It reads features from files as
GeoJSON-like mappings and writes the same kind of mappings as features back to
files. That's it. There are no layers, no cursors, no geometric operations, no
transformations between coordinate systems. Fiona doesn't just push the
complexity of OGR around, it tries to jettison as much of it as possible.

When would you want to use Fiona?

- If your data is in a RDBMS like PostGIS, use SQLAlchemy or GeoAlchemy.
- If your data is served via HTTP from CouchDB or CartoDB, etc, use httplib2 or
  the provider's Python API.
- If your data is in local files in shapefile, GPX, or other such formats, use
  Fiona.

Principles:

- Simpler is eventually better than easier.
- Python idioms like files and iterators trump GIS idioms like data sources and
  layers.
- Data are better than objects.

