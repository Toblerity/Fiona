=====
Fiona
=====

Fiona is OGR's neater API – sleek and elegant on the outside, indomitable power
on the inside.

Fiona provides a minimal, uncomplicated Python interface to the open source GIS
community's most trusted geodata access library and integrates readily with
other Python GIS packages such as pyproj_, Rtree_, and Shapely_.

How minimal? Fiona can read features as mappings from shapefiles or other GIS
vector formats and write mappings as features to files using the same formats.
That's all. There aren't any feature or geometry classes. Features and their
geometries are just data.

Dependencies
============

Fiona requires Python 2.6+ and libgdal 1.3.2+.

Building and testing
====================

Tests require Nose. From the distribution root::

  $ virtualenv .
  $ source bin/activate
  (Fiona)$ ./cypsrc
  (Fiona)$ python setup.py build_ext -I ${GDAL}/include -L ${GDAL}/lib develop
  (Fiona)$ python setup.py nosetests

If GDAL/OGR headers and libs aren't installed to a well known location, you'll
need to pass the locations in using setup arguments as shown above.

Usage
=====

Collections are much like ``file`` objects. Features are mappings modeled on
the GeoJSON format::

  from fiona import collection
  from shapely import asShape, mapping

  # Open a source of features
  with collection("docs/data/test_uk.shp", "r") as source:
  
      # Define a schema for the feature sink
      schema = input.schema.copy()
      schema['geometry'] = 'Point'
      
      # Open a new sink for features
      with collection(
              "test_write.shp", "w", driver="ESRI Shapefile", schema=schema
              ) as sink:
          
          # Process only the features intersecting a box
          for f in source.filter(bbox=(-5.0, 55.0, 0.0, 60.0)):
          
              # Get their centroids using Shapely
              f['geometry'] = mapping(asShape(f['geometry']).centroid)
              
              # Stage feature for writing
              sink.write(f)
              
      # The sink shapefile is written to disk when its ``with`` block ends

.. _libgdal: http://www.gdal.org
.. _pyproj: http://pypi.python.org/pypi/pyproj/
.. _Rtree: http://pypi.python.org/pypi/Rtree/
.. _Shapely: http://pypi.python.org/pypi/Shapely/

