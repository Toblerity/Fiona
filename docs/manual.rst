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

When would you want to use Fiona?

- If your data is in a RDBMS like PostGIS, use SQLAlchemy or GeoAlchemy.
- If your data is served via HTTP from CouchDB or CartoDB, etc, use httplib2 or
  the provider's Python API.
- If your data is in local files in shapefile, GPX, or other such formats, use
  Fiona.

