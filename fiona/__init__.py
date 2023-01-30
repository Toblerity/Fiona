# -*- coding: utf-8 -*-

"""
Fiona is OGR's neat, nimble API.

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
   'properties': {'label': 'Null Island'} }

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

import glob
import logging
import os
import warnings
import platform

try:
    from pathlib import Path
except ImportError:  # pragma: no cover
    class Path:
        pass

if platform.system() == "Windows":
    _whl_dir = os.path.join(os.path.dirname(__file__), ".libs")
    if os.path.exists(_whl_dir):
        os.add_dll_directory(_whl_dir)
    else:
        if "PATH" in os.environ:
            for p in os.environ["PATH"].split(os.pathsep):
                if glob.glob(os.path.join(p, "gdal*.dll")):
                    os.add_dll_directory(p)


from fiona._env import (
    calc_gdal_version_num,
    get_gdal_release_name,
    get_gdal_version_num,
    get_gdal_version_tuple,
)
from fiona._env import driver_count
from fiona._show_versions import show_versions
from fiona.collection import BytesCollection, Collection
from fiona.drvsupport import supported_drivers
from fiona.env import ensure_env_with_credentials, Env
from fiona.errors import FionaDeprecationWarning
from fiona.io import MemoryFile
from fiona.model import Feature, Geometry, Properties
from fiona.ogrext import (
    FIELD_TYPES_MAP,
    _bounds,
    _listdir,
    _listlayers,
    _remove,
    _remove_layer,
)
from fiona.path import ParsedPath, parse_path, vsi_path
from fiona.vfs import parse_paths as vfs_parse_paths

# These modules are imported by fiona.ogrext, but are also import here to
# help tools like cx_Freeze find them automatically
from fiona import _geometry, _err, rfc3339
import uuid


__all__ = [
    "Feature",
    "Geometry",
    "Properties",
    "bounds",
    "listlayers",
    "listdir",
    "open",
    "prop_type",
    "prop_width",
]
__version__ = "1.9.0"
__gdal_version__ = get_gdal_release_name()

gdal_version = get_gdal_version_tuple()

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


@ensure_env_with_credentials
def open(
    fp,
    mode="r",
    driver=None,
    schema=None,
    crs=None,
    encoding=None,
    layer=None,
    vfs=None,
    enabled_drivers=None,
    crs_wkt=None,
    allow_unsupported_drivers=False,
    **kwargs
):
    """Open a collection for read, append, or write

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

    Parameters
    ----------
    fp : URI (str or pathlib.Path), or file-like object
        A dataset resource identifier or file object.
    mode : str
        One of 'r', to read (the default); 'a', to append; or 'w', to
        write.
    driver : str
        In 'w' mode a format driver name is required. In 'r' or 'a'
        mode this parameter has no effect.
    schema : dict
        Required in 'w' mode, has no effect in 'r' or 'a' mode.
    crs : str or dict
        Required in 'w' mode, has no effect in 'r' or 'a' mode.
    encoding : str
        Name of the encoding used to encode or decode the dataset.
    layer : int or str
        The integer index or name of a layer in a multi-layer dataset.
    vfs : str
        This is a deprecated parameter. A URI scheme such as "zip://"
        should be used instead.
    enabled_drivers : list
        An optional list of driver names to used when opening a
        collection.
    crs_wkt : str
        An optional WKT representation of a coordinate reference
        system.
    ignore_fields : list
        List of field names to ignore on load.
    ignore_geometry : bool
        Ignore the geometry on load.
    include_fields : list
        List of a subset of field names to include on load.
    wkt_version : fiona.enums.WktVersion or str, optional
        Version to use to for the CRS WKT.
        Defaults to GDAL's default (WKT1_GDAL for GDAL 3).
    allow_unsupported_drivers : bool
        If set to true do not limit GDAL drivers to set set of known working.
    kwargs : mapping
        Other driver-specific parameters that will be interpreted by
        the OGR library as layer creation or opening options.

    Returns
    -------
    Collection

    """
    if mode == "r" and hasattr(fp, "read"):
        memfile = MemoryFile(fp.read())
        colxn = memfile.open(
            driver=driver,
            crs=crs,
            schema=schema,
            layer=layer,
            encoding=encoding,
            enabled_drivers=enabled_drivers,
            allow_unsupported_drivers=allow_unsupported_drivers,
            **kwargs
        )
        colxn._env.enter_context(memfile)
        return colxn

    elif mode == "w" and hasattr(fp, "write"):
        memfile = MemoryFile()
        colxn = memfile.open(
            driver=driver,
            crs=crs,
            schema=schema,
            layer=layer,
            encoding=encoding,
            enabled_drivers=enabled_drivers,
            allow_unsupported_drivers=allow_unsupported_drivers,
            crs_wkt=crs_wkt,
            **kwargs
        )
        colxn._env.enter_context(memfile)

        # For the writing case we push an extra callback onto the
        # ExitStack. It ensures that the MemoryFile's contents are
        # copied to the open file object.
        def func(*args, **kwds):
            memfile.seek(0)
            fp.write(memfile.read())

        colxn._env.callback(func)
        return colxn

    elif mode == "a" and hasattr(fp, "write"):
        raise OSError(
            "Append mode is not supported for datasets in a Python file object."
        )

    # TODO: test for a shared base class or abstract type.
    elif isinstance(fp, MemoryFile):
        if mode.startswith("r"):
            colxn = fp.open(
                driver=driver,
                allow_unsupported_drivers=allow_unsupported_drivers,
                **kwargs
            )

        # Note: FilePath does not support writing and an exception will
        # result from this.
        elif mode.startswith("w"):
            colxn = fp.open(
                driver=driver,
                crs=crs,
                schema=schema,
                layer=layer,
                encoding=encoding,
                enabled_drivers=enabled_drivers,
                allow_unsupported_drivers=allow_unsupported_drivers,
                crs_wkt=crs_wkt,
                **kwargs
            )
        return colxn

    # At this point, the fp argument is a string or path-like object
    # which can be converted to a string.
    else:
        # If a pathlib.Path instance is given, convert it to a string path.
        if isinstance(fp, Path):
            fp = str(fp)

        if vfs:
            warnings.warn(
                "The vfs keyword argument is deprecated and will be removed in version 2.0.0. Instead, pass a URL that uses a zip or tar (for example) scheme.",
                FionaDeprecationWarning,
                stacklevel=2,
            )
            path, scheme, archive = vfs_parse_paths(fp, vfs=vfs)
            path = ParsedPath(path, archive, scheme)
        else:
            path = parse_path(fp)

        if mode in ("a", "r"):
            colxn = Collection(
                path,
                mode,
                driver=driver,
                encoding=encoding,
                layer=layer,
                enabled_drivers=enabled_drivers,
                allow_unsupported_drivers=allow_unsupported_drivers,
                **kwargs
            )
        elif mode == "w":
            colxn = Collection(
                path,
                mode,
                crs=crs,
                driver=driver,
                schema=schema,
                encoding=encoding,
                layer=layer,
                enabled_drivers=enabled_drivers,
                crs_wkt=crs_wkt,
                allow_unsupported_drivers=allow_unsupported_drivers,
                **kwargs
            )
        else:
            raise ValueError("mode string must be one of {'r', 'w', 'a'}")

        return colxn


collection = open


def remove(path_or_collection, driver=None, layer=None):
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
    if layer is None:
        _remove(path, driver)
    else:
        _remove_layer(path, layer, driver)


def listdir(path):
    """List files in a directory
    Parameters
    ----------
    path : URI (str or pathlib.Path)
        A dataset resource identifier.
    Returns
    -------
    list
        A list of filename strings.
    """
    if isinstance(path, Path):
        path = str(path)
    if not isinstance(path, str):
        raise TypeError("invalid path: %r" % path)
    pobj = parse_path(path)
    return _listdir(vsi_path(pobj))


@ensure_env_with_credentials
def listlayers(fp, vfs=None):
    """List layer names in their index order

    Parameters
    ----------
    fp : URI (str or pathlib.Path), or file-like object
        A dataset resource identifier or file object.
    vfs : str
        This is a deprecated parameter. A URI scheme such as "zip://"
        should be used instead.

    Returns
    -------
    list
        A list of layer name strings.

    """
    if hasattr(fp, 'read'):

        with MemoryFile(fp.read()) as memfile:
            return _listlayers(memfile.name)

    else:

        if isinstance(fp, Path):
            fp = str(fp)

        if not isinstance(fp, str):
            raise TypeError("invalid path: %r" % fp)
        if vfs and not isinstance(vfs, str):
            raise TypeError("invalid vfs: %r" % vfs)

        if vfs:
            warnings.warn("The vfs keyword argument is deprecated. Instead, pass a URL that uses a zip or tar (for example) scheme.", FionaDeprecationWarning, stacklevel=2)
            pobj_vfs = parse_path(vfs)
            pobj_path = parse_path(fp)
            pobj = ParsedPath(pobj_path.path, pobj_vfs.path, pobj_vfs.scheme)
        else:
            pobj = parse_path(fp)

        return _listlayers(vsi_path(pobj))


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
    """Returns a context manager with registered drivers.

    DEPRECATED
    """
    warnings.warn("Use fiona.Env() instead.", FionaDeprecationWarning, stacklevel=2)

    if driver_count == 0:
        log.debug("Creating a chief GDALEnv in drivers()")
        return Env(**kwargs)
    else:
        log.debug("Creating a not-responsible GDALEnv in drivers()")
        return Env(**kwargs)


def bounds(ob):
    """Returns a (minx, miny, maxx, maxy) bounding box.

    The ``ob`` may be a feature record or geometry."""
    geom = ob.get('geometry') or ob
    return _bounds(geom)
