=====
Fiona
=====

Fiona is OGR's neater API – sleek elegance on the outside, unstoppable OGR(e)
on the inside.

Fiona provides a smoother and more productive Python interface to the open
source GIS community's most trusted geodata access library; doing for libgdal_
what lxml does for libxml2. Fiona integrates readily with other Python GIS
packages such as pyproj_, Rtree_, and Shapely_.

Dependencies
============

Fiona requires libgdal 1.3.2+.

Building and testing
====================

Tests require Nose. From the distribution root::

  $ virtualenv .
  $ source bin/activate
  (Fiona)$ ./cypsrc
  (Fiona)$ python setup.py develop
  (Fiona)$ python setup.py nosetests

If GDAL/OGR headers and libs aren't installed to a well known location, you'll
need to set environment variables before running the setup script or pass the
locations in using setup arguments.

If you have osgeo.ogr installed, you can compare performance to Fiona::

  $ python benchmark.py

Usage
=====

See `docs/reading-data.txt`_ for examples.

.. _libgdal: http://www.gdal.org
.. _pyproj: http://pypi.python.org/pypi/pyproj/
.. _Rtree: http://pypi.python.org/pypi/Rtree/
.. _Shapely: http://pypi.python.org/pypi/Shapely/
.. _docs/reading-data.txt: https://github.com/sgillies/Fiona/blob/master/docs/reading-data.txt
