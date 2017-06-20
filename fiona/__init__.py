# -*- coding: utf-8 -*-

"""
Fiona is OGR's neat, nimble, no-nonsense API.

Fiona provides a minimal, uncomplicated Python interface to the open
source GIS community's most trusted geodata access library and
integrates readily with other Python GIS packages such as pyproj, Rtree
and Shapely.

How minimal? Fiona can read features as mappings from shapefiles or
other GIS vector formats and write mappings as features to files using
the same formats. That's all. There aren't any feature or geometry
classes. Features and their geometries are just data.

A Fiona feature is a Python mapping inspired by the GeoJSON format. It
has `id`, 'geometry`, and `properties` keys. The value of `id` is
a string identifier unique within the feature's parent collection. The
`geometry` is another mapping with `type` and `coordinates` keys. The
`properties` of a feature is another mapping corresponding to its
attribute table. For example:

  {'id': '1',
   'geometry': {'type': 'Point', 'coordinates': (0.0, 0.0)},
   'properties': {'label': u'Null Island'} }

is a Fiona feature with a point geometry and one property.

Features are read and written using objects returned by the
``collection`` function. These ``Collection`` objects are a lot like
Python ``file`` objects. A ``Collection`` opened in reading mode serves
as an iterator over features. One opened in a writing mode provides
a ``write`` method.

Usage
-----

Here's an example of reading a select few polygon features from
a shapefile and for each, picking off the first vertex of the exterior
ring of the polygon and using that as the point geometry for a new
feature writing to a "points.shp" file.

  >>> import fiona
  >>> with fiona.open('docs/data/test_uk.shp', 'r') as inp:
  ...     output_schema = inp.schema.copy()
  ...     output_schema['geometry'] = 'Point'
  ...     with collection(
  ...             "points.shp", "w",
  ...             crs=inp.crs,
  ...             driver="ESRI Shapefile",
  ...             schema=output_schema
  ...             ) as out:
  ...         for f in inp.filter(
  ...                 bbox=(-5.0, 55.0, 0.0, 60.0)
  ...                 ):
  ...             value = f['geometry']['coordinates'][0][0]
  ...             f['geometry'] = {
  ...                 'type': 'Point', 'coordinates': value}
  ...             out.write(f)

Because Fiona collections are context managers, they are closed and (in
writing modes) flush contents to disk when their ``with`` blocks end.
"""

import logging
import os
from six import string_types

from fiona.collection import Collection, BytesCollection, vsi_path
from fiona._drivers import driver_count, GDALEnv
from fiona.drvsupport import supported_drivers
from fiona.compat import OrderedDict
from fiona.ogrext import _bounds, _listlayers, FIELD_TYPES_MAP, _remove
from fiona.ogrext import (
    calc_gdal_version_num, get_gdal_version_num, get_gdal_release_name)

# These modules are imported by fiona.ogrext, but are also import here to
# help tools like cx_Freeze find them automatically
from fiona import _geometry, _err, rfc3339
import uuid


__all__ = ['bounds', 'listlayers', 'open', 'prop_type', 'prop_width']
__version__ = "1.7.8"
__gdal_version__ = get_gdal_release_name().decode('utf-8')

log = logging.getLogger(__name__)


def open(
        path,
        mode='r',
        driver=None,
        schema=None,
        crs=None,
        encoding=None,
        layer=None,
        vfs=None,
        enabled_drivers=None,
        crs_wkt=None):
    """Open file at ``path`` in ``mode`` "r" (read), "a" (append), or
    "w" (write) and return a ``Collection`` object.

    In write mode, a driver name such as "ESRI Shapefile" or "GPX" (see
    OGR docs or ``ogr2ogr --help`` on the command line) and a schema
    mapping such as:

      {'geometry': 'Point',
       'properties': [('class', 'int'), ('label', 'str'),
                      ('value', 'float')]}

    must be provided. If a particular ordering of properties ("fields"
    in GIS parlance) in the written file is desired, a list of (key,
    value) pairs as above or an ordered dict is required. If no ordering
    is needed, a standard dict will suffice.

    A coordinate reference system for collections in write mode can be
    defined by the ``crs`` parameter. It takes Proj4 style mappings like

      {'proj': 'longlat', 'ellps': 'WGS84', 'datum': 'WGS84',
       'no_defs': True}

    short hand strings like

      EPSG:4326

    or WKT representations of coordinate reference systems.

    The drivers used by Fiona will try to detect the encoding of data
    files. If they fail, you may provide the proper ``encoding``, such
    as 'Windows-1252' for the Natural Earth datasets.

    When the provided path is to a file containing multiple named layers
    of data, a layer can be singled out by ``layer``.

    A virtual filesystem can be specified. The ``vfs`` parameter may be
    an Apache Commons VFS style string beginning with "zip://" or
    "tar://"". In this case, the ``path`` must be an absolute path
    within that container.

    The drivers enabled for opening datasets may be restricted to those
    listed in the ``enabled_drivers`` parameter. This and the ``driver``
    parameter afford much control over opening of files.

      # Trying only the GeoJSON driver when opening to read, the
      # following raises ``DataIOError``:
      fiona.open('example.shp', driver='GeoJSON')

      # Trying first the GeoJSON driver, then the Shapefile driver,
      # the following succeeds:
      fiona.open(
          'example.shp', enabled_drivers=['GeoJSON', 'ESRI Shapefile'])

    """
    # Parse the vfs into a vsi and an archive path.
    path, vsi, archive = parse_paths(path, vfs)
    if mode in ('a', 'r'):
        if archive:
            if not os.path.exists(archive):
                raise IOError("no such archive file: %r" % archive)
        elif path != '-' and not os.path.exists(path):
            raise IOError("no such file or directory: %r" % path)
        c = Collection(path, mode, driver=driver, encoding=encoding,
                       layer=layer, vsi=vsi, archive=archive,
                       enabled_drivers=enabled_drivers)
    elif mode == 'w':
        if schema:
            # Make an ordered dict of schema properties.
            this_schema = schema.copy()
            this_schema['properties'] = OrderedDict(schema['properties'])
        else:
            this_schema = None
        c = Collection(path, mode, crs=crs, driver=driver, schema=this_schema,
                       encoding=encoding, layer=layer, vsi=vsi, archive=archive,
                       enabled_drivers=enabled_drivers, crs_wkt=crs_wkt)
    else:
        raise ValueError(
            "mode string must be one of 'r', 'w', or 'a', not %s" % mode)
    return c

collection = open


def remove(path_or_collection, driver=None):
    """Deletes an OGR data source

    The required ``path`` argument may be an absolute or relative file path.
    Alternatively, a Collection can be passed instead in which case the path
    and driver are automatically determined. Otherwise the ``driver`` argument
    must be specified.

    Raises a ``RuntimeError`` if the data source cannot be deleted.

    Example usage:

      fiona.remove('test.shp', 'ESRI Shapefile')

    """
    if isinstance(path_or_collection, Collection):
        collection = path_or_collection
        path = collection.path
        driver = collection.driver
        collection.close()
    else:
        path = path_or_collection
        if driver is None:
            raise ValueError("The driver argument is required when removing a path")
    _remove(path, driver)


def listlayers(path, vfs=None):
    """Returns a list of layer names in their index order.

    The required ``path`` argument may be an absolute or relative file or
    directory path.

    A virtual filesystem can be specified. The ``vfs`` parameter may be
    an Apache Commons VFS style string beginning with "zip://" or
    "tar://"". In this case, the ``path`` must be an absolute path within
    that container.
    """
    if not isinstance(path, string_types):
        raise TypeError("invalid path: %r" % path)
    if vfs and not isinstance(vfs, string_types):
        raise TypeError("invalid vfs: %r" % vfs)

    path, vsi, archive = parse_paths(path, vfs)

    if archive:
        if not os.path.exists(archive):
            raise IOError("no such archive file: %r" % archive)
    elif not os.path.exists(path):
        raise IOError("no such file or directory: %r" % path)

    with drivers():
        return _listlayers(vsi_path(path, vsi, archive))


def parse_paths(path, vfs=None):
    archive = vsi = None
    if vfs:
        parts = vfs.split("://")
        vsi = parts.pop(0) if parts else None
        archive = parts.pop(0) if parts else None
    else:
        parts = path.split("://")
        path = parts.pop() if parts else None
        vsi = parts.pop() if parts else None
    return path, vsi, archive


def prop_width(val):
    """Returns the width of a str type property.

    Undefined for non-str properties. Example:

      >>> prop_width('str:25')
      25
      >>> prop_width('str')
      80
    """
    if val.startswith('str'):
        return int((val.split(":")[1:] or ["80"])[0])
    return None


def prop_type(text):
    """Returns a schema property's proper Python type.

    Example:

      >>> prop_type('int')
      <class 'int'>
      >>> prop_type('str:25')
      <class 'str'>
    """
    key = text.split(':')[0]
    return FIELD_TYPES_MAP[key]


def drivers(*args, **kwargs):
    """Returns a context manager with registered drivers."""
    if driver_count == 0:
        log.debug("Creating a chief GDALEnv in drivers()")
        return GDALEnv(**kwargs)
    else:
        log.debug("Creating a not-responsible GDALEnv in drivers()")
        return GDALEnv(**kwargs)


def bounds(ob):
    """Returns a (minx, miny, maxx, maxy) bounding box.

    The ``ob`` may be a feature record or geometry."""
    geom = ob.get('geometry') or ob
    return _bounds(geom)
