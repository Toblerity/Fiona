# -*- coding: utf-8 -*-
# Collections provide file-like access to feature data

import logging
import os
import warnings

import fiona._loading
with fiona._loading.add_gdal_dll_directories():
    from fiona import compat, vfs
    from fiona.ogrext import Iterator, ItemsIterator, KeysIterator
    from fiona.ogrext import Session, WritingSession
    from fiona.ogrext import buffer_to_virtual_file, remove_virtual_file, GEOMETRY_TYPES
    from fiona.errors import (DriverError, SchemaError, CRSError, UnsupportedGeometryTypeError, DriverSupportError)
    from fiona.logutils import FieldSkipLogFilter
    from fiona._crs import crs_to_wkt
    from fiona._env import get_gdal_release_name, get_gdal_version_tuple
    from fiona.env import env_ctx_if_needed
    from fiona.errors import FionaDeprecationWarning
    from fiona.drvsupport import (supported_drivers, driver_mode_mingdal, _driver_converts_field_type_silently_to_str,
                                  _driver_supports_field)
    from fiona.path import Path, vsi_path, parse_path
    from six import string_types, binary_type


log = logging.getLogger(__name__)


class Collection(object):

    """A file-like interface to features of a vector dataset

    Python text file objects are iterators over lines of a file. Fiona
    Collections are similar iterators (not lists!) over features
    represented as GeoJSON-like mappings.
    """

    def __init__(self, path, mode='r', driver=None, schema=None, crs=None,
                 encoding=None, layer=None, vsi=None, archive=None,
                 enabled_drivers=None, crs_wkt=None, ignore_fields=None,
                 ignore_geometry=False,
                 **kwargs):

        """The required ``path`` is the absolute or relative path to
        a file, such as '/data/test_uk.shp'. In ``mode`` 'r', data can
        be read only. In ``mode`` 'a', data can be appended to a file.
        In ``mode`` 'w', data overwrites the existing contents of
        a file.

        In ``mode`` 'w', an OGR ``driver`` name and a ``schema`` are
        required. A Proj4 ``crs`` string is recommended. If both ``crs``
        and ``crs_wkt`` keyword arguments are passed, the latter will
        trump the former.

        In 'w' mode, kwargs will be mapped to OGR layer creation
        options.
        """

        if not isinstance(path, (string_types, Path)):
            raise TypeError("invalid path: %r" % path)
        if not isinstance(mode, string_types) or mode not in ('r', 'w', 'a'):
            raise TypeError("invalid mode: %r" % mode)
        if driver and not isinstance(driver, string_types):
            raise TypeError("invalid driver: %r" % driver)
        if schema and not hasattr(schema, 'get'):
            raise TypeError("invalid schema: %r" % schema)
        if crs and not isinstance(crs, compat.DICT_TYPES + string_types):
            raise TypeError("invalid crs: %r" % crs)
        if crs_wkt and not isinstance(crs_wkt, string_types):
            raise TypeError("invalid crs_wkt: %r" % crs_wkt)
        if encoding and not isinstance(encoding, string_types):
            raise TypeError("invalid encoding: %r" % encoding)
        if layer and not isinstance(layer, tuple(list(string_types) + [int])):
            raise TypeError("invalid name: %r" % layer)
        if vsi:
            if not isinstance(vsi, string_types) or not vfs.valid_vsi(vsi):
                raise TypeError("invalid vsi: %r" % vsi)
        if archive and not isinstance(archive, string_types):
            raise TypeError("invalid archive: %r" % archive)

        self.session = None
        self.iterator = None
        self._len = 0
        self._bounds = None
        self._driver = None
        self._schema = None
        self._crs = None
        self._crs_wkt = None
        self.env = None
        self.enabled_drivers = enabled_drivers
        self.ignore_fields = ignore_fields
        self.ignore_geometry = bool(ignore_geometry)

        # Check GDAL version against drivers
        if driver in driver_mode_mingdal[mode] and get_gdal_version_tuple() < driver_mode_mingdal[mode][driver]:
            min_gdal_version = ".".join(list(map(str, driver_mode_mingdal[mode][driver])))

            raise DriverError(
                "{driver} driver requires at least GDAL {min_gdal_version} for mode '{mode}', "
                "Fiona was compiled against: {gdal}".format(driver=driver,
                                                            mode=mode,
                                                            min_gdal_version=min_gdal_version,
                                                            gdal=get_gdal_release_name()))

        if vsi:
            self.path = vfs.vsi_path(path, vsi, archive)
            path = parse_path(self.path)
        else:
            path = parse_path(path)
            self.path = vsi_path(path)

        if mode == 'w':
            if layer and not isinstance(layer, string_types):
                raise ValueError("in 'w' mode, layer names must be strings")
            if driver == 'GeoJSON':
                if layer is not None:
                    raise ValueError("the GeoJSON format does not have layers")
                self.name = 'OgrGeoJSON'
            # TODO: raise ValueError as above for other single-layer formats.
            else:
                self.name = layer or os.path.basename(os.path.splitext(path.path)[0])
        else:
            if layer in (0, None):
                self.name = 0
            else:
                self.name = layer or os.path.basename(os.path.splitext(path)[0])

        self.mode = mode

        if self.mode == 'w':
            if driver == 'Shapefile':
                driver = 'ESRI Shapefile'
            if not driver:
                raise DriverError("no driver")
            elif driver not in supported_drivers:
                raise DriverError(
                    "unsupported driver: %r" % driver)
            elif self.mode not in supported_drivers[driver]:
                raise DriverError(
                    "unsupported mode: %r" % self.mode)
            self._driver = driver

            if not schema:
                raise SchemaError("no schema")
            elif 'properties' not in schema:
                raise SchemaError("schema lacks: properties")
            elif 'geometry' not in schema:
                raise SchemaError("schema lacks: geometry")
            self._schema = schema

            self._check_schema_driver_support()
            if crs_wkt or crs:
                self._crs_wkt = crs_to_wkt(crs_wkt or crs)

        self._driver = driver
        kwargs.update(encoding=encoding)
        self.encoding = encoding

        try:
            if self.mode == 'r':
                self.session = Session()
                self.session.start(self, **kwargs)
            elif self.mode in ('a', 'w'):
                self.session = WritingSession()
                self.session.start(self, **kwargs)
        except IOError:
            self.session = None
            raise

        if self.session is not None:
            self.guard_driver_mode()

        if self.mode in ("a", "w"):
            self._valid_geom_types = _get_valid_geom_types(self.schema, self.driver)

        self.field_skip_log_filter = FieldSkipLogFilter()

    def __repr__(self):
        return "<%s Collection '%s', mode '%s' at %s>" % (
            self.closed and "closed" or "open",
            self.path + ":" + str(self.name),
            self.mode,
            hex(id(self)))

    def guard_driver_mode(self):
        driver = self.session.get_driver()
        if driver not in supported_drivers:
            raise DriverError("unsupported driver: %r" % driver)
        if self.mode not in supported_drivers[driver]:
            raise DriverError("unsupported mode: %r" % self.mode)

    @property
    def driver(self):
        """Returns the name of the proper OGR driver."""
        if not self._driver and self.mode in ("a", "r") and self.session:
            self._driver = self.session.get_driver()
        return self._driver

    @property
    def schema(self):
        """Returns a mapping describing the data schema.

        The mapping has 'geometry' and 'properties' items. The former is a
        string such as 'Point' and the latter is an ordered mapping that
        follows the order of fields in the data file.
        """
        if not self._schema and self.mode in ("a", "r") and self.session:
            self._schema = self.session.get_schema()
        return self._schema

    @property
    def crs(self):
        """Returns a Proj4 string."""
        if self._crs is None and self.session:
            self._crs = self.session.get_crs()
        return self._crs

    @property
    def crs_wkt(self):
        """Returns a WKT string."""
        if self._crs_wkt is None and self.session:
            self._crs_wkt = self.session.get_crs_wkt()
        return self._crs_wkt

    @property
    def meta(self):
        """Returns a mapping with the driver, schema, crs, and additional
        properties."""
        return {
            'driver': self.driver, 'schema': self.schema, 'crs': self.crs,
            'crs_wkt': self.crs_wkt}

    profile = meta

    def filter(self, *args, **kwds):
        """Returns an iterator over records, but filtered by a test for
        spatial intersection with the provided ``bbox``, a (minx, miny,
        maxx, maxy) tuple or a geometry ``mask``.

        Positional arguments ``stop`` or ``start, stop[, step]`` allows
        iteration to skip over items or stop at a specific item.

        Note: spatial filtering using ``mask`` may be inaccurate and returning
        all features overlapping the envelope of ``mask``.

        """
        if self.closed:
            raise ValueError("I/O operation on closed collection")
        elif self.mode != 'r':
            raise IOError("collection not open for reading")
        if args:
            s = slice(*args)
            start = s.start
            stop = s.stop
            step = s.step
        else:
            start = stop = step = None
        bbox = kwds.get('bbox')
        mask = kwds.get('mask')
        if bbox and mask:
            raise ValueError("mask and bbox can not be set together")
        self.iterator = Iterator(
            self, start, stop, step, bbox, mask)
        return self.iterator

    def items(self, *args, **kwds):
        """Returns an iterator over FID, record pairs, optionally
        filtered by a test for spatial intersection with the provided
        ``bbox``, a (minx, miny, maxx, maxy) tuple or a geometry
        ``mask``.

        Positional arguments ``stop`` or ``start, stop[, step]`` allows
        iteration to skip over items or stop at a specific item.

        Note: spatial filtering using ``mask`` may be inaccurate and returning
        all features overlapping the envelope of ``mask``.

        """
        if self.closed:
            raise ValueError("I/O operation on closed collection")
        elif self.mode != 'r':
            raise IOError("collection not open for reading")
        if args:
            s = slice(*args)
            start = s.start
            stop = s.stop
            step = s.step
        else:
            start = stop = step = None
        bbox = kwds.get('bbox')
        mask = kwds.get('mask')
        if bbox and mask:
            raise ValueError("mask and bbox can not be set together")
        self.iterator = ItemsIterator(
            self, start, stop, step, bbox, mask)
        return self.iterator

    def keys(self, *args, **kwds):
        """Returns an iterator over FIDs, optionally
        filtered by a test for spatial intersection with the provided
        ``bbox``, a (minx, miny, maxx, maxy) tuple or a geometry
        ``mask``.

        Positional arguments ``stop`` or ``start, stop[, step]`` allows
        iteration to skip over items or stop at a specific item.

        Note: spatial filtering using ``mask`` may be inaccurate and returning
        all features overlapping the envelope of ``mask``.
        """
        if self.closed:
            raise ValueError("I/O operation on closed collection")
        elif self.mode != 'r':
            raise IOError("collection not open for reading")
        if args:
            s = slice(*args)
            start = s.start
            stop = s.stop
            step = s.step
        else:
            start = stop = step = None
        bbox = kwds.get('bbox')
        mask = kwds.get('mask')
        if bbox and mask:
            raise ValueError("mask and bbox can not be set together")
        self.iterator = KeysIterator(
            self, start, stop, step, bbox, mask)
        return self.iterator

    def __contains__(self, fid):
        return self.session.has_feature(fid)

    values = filter

    def __iter__(self):
        """Returns an iterator over records."""
        return self.filter()

    def __next__(self):
        """Returns next record from iterator."""
        warnings.warn("Collection.__next__() is buggy and will be removed in "
                      "Fiona 2.0. Switch to `next(iter(collection))`.",
                      FionaDeprecationWarning, stacklevel=2)
        if not self.iterator:
            iter(self)
        return next(self.iterator)

    next = __next__

    def __getitem__(self, item):
        return self.session.__getitem__(item)

    def get(self, item):
        return self.session.get(item)

    def writerecords(self, records):
        """Stages multiple records for writing to disk."""
        if self.closed:
            raise ValueError("I/O operation on closed collection")
        if self.mode not in ('a', 'w'):
            raise IOError("collection not open for writing")
        self.session.writerecs(records, self)
        self._len = self.session.get_length()
        self._bounds = None

    def write(self, record):
        """Stages a record for writing to disk."""
        self.writerecords([record])

    def validate_record(self, record):
        """Compares the record to the collection's schema.

        Returns ``True`` if the record matches, else ``False``.
        """
        # Currently we only compare keys of properties, not the types of
        # values.
        return (
            set(record['properties'].keys()) ==
            set(self.schema['properties'].keys()) and
            self.validate_record_geometry(record))

    def validate_record_geometry(self, record):
        """Compares the record's geometry to the collection's schema.

        Returns ``True`` if the record matches, else ``False``.
        """
        # Shapefiles welcome mixes of line/multis and polygon/multis.
        # OGR reports these mixed files as type "Polygon" or "LineString"
        # but will return either these or their multi counterparts when
        # reading features.
        if (self.driver == "ESRI Shapefile" and
                "Point" not in record['geometry']['type']):
            return record['geometry']['type'].lstrip(
                "Multi") == self.schema['geometry'].lstrip("3D ").lstrip(
                    "Multi")
        else:
            return (
                record['geometry']['type'] ==
                self.schema['geometry'].lstrip("3D "))

    def __len__(self):
        if self._len <= 0 and self.session is not None:
            self._len = self.session.get_length()
        if self._len < 0:
            # Raise TypeError when we don't know the length so that Python
            # will treat Collection as a generator
            raise TypeError("Layer does not support counting")
        return self._len

    @property
    def bounds(self):
        """Returns (minx, miny, maxx, maxy)."""
        if self._bounds is None and self.session is not None:
            self._bounds = self.session.get_extent()
        return self._bounds

    def _check_schema_driver_support(self):
        """Check support for the schema against the driver

        See GH#572 for discussion.
        """
        gdal_version_major = get_gdal_version_tuple().major

        for field in self._schema["properties"].values():
            field_type = field.split(":")[0]

            if not _driver_supports_field(self.driver, field_type):
                if self.driver == 'GPKG' and gdal_version_major < 2 and field_type == "datetime":
                    raise DriverSupportError("GDAL 1.x GPKG driver does not support datetime fields")
                else:
                    raise DriverSupportError("{driver} does not support {field_type} "
                                             "fields".format(driver=self.driver,
                                                             field_type=field_type))
            elif field_type in {'time', 'datetime', 'date'} and _driver_converts_field_type_silently_to_str(self.driver,
                                                                                                           field_type):
                if self._driver == "GeoJSON" and gdal_version_major < 2 and field_type in {'datetime', 'date'}:
                    warnings.warn("GeoJSON driver in GDAL 1.x silently converts {} to string"
                                  " in non-standard format".format(field_type))
                else:
                    warnings.warn("{driver} driver silently converts {field_type} "
                                  "to string".format(driver=self.driver,
                                                     field_type=field_type))

    def flush(self):
        """Flush the buffer."""
        if self.session is not None:
            self.session.sync(self)
            new_len = self.session.get_length()
            self._len = new_len > self._len and new_len or self._len
            self._bounds = None

    def close(self):
        """In append or write mode, flushes data to disk, then ends
        access."""
        if self.session is not None and self.session.isactive():
            if self.mode in ('a', 'w'):
                self.flush()
            log.debug("Flushed buffer")
            self.session.stop()
            log.debug("Stopped session")
            self.session = None
            self.iterator = None
        if self.env:
            self.env.__exit__()

    @property
    def closed(self):
        """``False`` if data can be accessed, otherwise ``True``."""
        return self.session is None

    def __enter__(self):
        logging.getLogger('fiona.ogrext').addFilter(self.field_skip_log_filter)
        self._env = env_ctx_if_needed()
        self._env.__enter__()
        return self

    def __exit__(self, type, value, traceback):
        logging.getLogger('fiona.ogrext').removeFilter(self.field_skip_log_filter)
        self._env.__exit__()
        self.close()

    def __del__(self):
        # Note: you can't count on this being called. Call close() explicitly
        # or use the context manager protocol ("with").
        self.close()


ALL_GEOMETRY_TYPES = set([
    geom_type for geom_type in GEOMETRY_TYPES.values()
    if "3D " not in geom_type and geom_type != "None"])
ALL_GEOMETRY_TYPES.add("None")


def _get_valid_geom_types(schema, driver):
    """Returns a set of geometry types the schema will accept"""
    schema_geom_type = schema["geometry"]
    if isinstance(schema_geom_type, string_types) or schema_geom_type is None:
        schema_geom_type = (schema_geom_type,)
    valid_types = set()
    for geom_type in schema_geom_type:
        geom_type = str(geom_type).lstrip("3D ")
        if geom_type == "Unknown" or geom_type == "Any":
            valid_types.update(ALL_GEOMETRY_TYPES)
        else:
            if geom_type not in ALL_GEOMETRY_TYPES:
                raise UnsupportedGeometryTypeError(geom_type)
            valid_types.add(geom_type)

    # shapefiles don't differentiate between single/multi geometries, except points
    if driver == "ESRI Shapefile" and "Point" not in valid_types:
        for geom_type in list(valid_types):
            if not geom_type.startswith("Multi"):
                valid_types.add("Multi" + geom_type)

    return valid_types


def get_filetype(bytesbuf):
    """Detect compression type of bytesbuf.

    ZIP only. TODO: add others relevant to GDAL/OGR."""
    if bytesbuf[:4].startswith(b'PK\x03\x04'):
        return 'zip'
    else:
        return ''


class BytesCollection(Collection):
    """BytesCollection takes a buffer of bytes and maps that to
    a virtual file that can then be opened by fiona.
    """
    def __init__(self, bytesbuf, **kwds):
        """Takes buffer of bytes whose contents is something we'd like
        to open with Fiona and maps it to a virtual file.
        """
        if not isinstance(bytesbuf, binary_type):
            raise ValueError("input buffer must be bytes")

        # Hold a reference to the buffer, as bad things will happen if
        # it is garbage collected while in use.
        self.bytesbuf = bytesbuf

        # Map the buffer to a file. If the buffer contains a zipfile
        # we take extra steps in naming the buffer and in opening
        # it. If the requested driver is for GeoJSON, we append an an
        # appropriate extension to ensure the driver reads it.
        filetype = get_filetype(self.bytesbuf)
        ext = ''
        if filetype == 'zip':
            ext = '.zip'
        elif kwds.get('driver') == "GeoJSON":
            ext = '.json'
        self.virtual_file = buffer_to_virtual_file(self.bytesbuf, ext=ext)

        # Instantiate the parent class.
        super(BytesCollection, self).__init__(self.virtual_file, vsi=filetype, **kwds)

    def close(self):
        """Removes the virtual file associated with the class."""
        super(BytesCollection, self).close()
        if self.virtual_file:
            remove_virtual_file(self.virtual_file)
            self.virtual_file = None
            self.bytesbuf = None

    def __repr__(self):
        return "<%s BytesCollection '%s', mode '%s' at %s>" % (
            self.closed and "closed" or "open",
            self.path + ":" + str(self.name),
            self.mode,
            hex(id(self)))
