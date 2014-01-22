# -*- coding: utf-8 -*-
# Collections provide file-like access to feature data

import os
import sys

from fiona.ogrext import Iterator, Session, WritingSession
from fiona.errors import DriverError, SchemaError, CRSError
from fiona._drivers import DriverManager, driver_count
from six import string_types

class Collection(object):

    """A file-like interface to features in the form of GeoJSON-like
    mappings."""

    def __init__(
            self, path, mode='r', 
            driver=None, schema=None, crs=None, 
            encoding=None,
            layer=None,
            vsi=None,
            archive=None,
            **kwargs):
        
        """The required ``path`` is the absolute or relative path to
        a file, such as '/data/test_uk.shp'. In ``mode`` 'r', data can
        be read only. In ``mode`` 'a', data can be appended to a file.
        In ``mode`` 'w', data overwrites the existing contents of
        a file.
        
        In ``mode`` 'w', an OGR ``driver`` name and a ``schema`` are
        required. A Proj4 ``crs`` string is recommended.
        
        In 'w' mode, kwargs will be mapped to OGR layer creation
        options.
        """
        if not isinstance(path, string_types):
            raise TypeError("invalid path: %r" % path)
        if not isinstance(mode, string_types) or mode not in ('r', 'w', 'a'):
            raise TypeError("invalid mode: %r" % mode)
        if driver and not isinstance(driver, string_types):
            raise TypeError("invalid driver: %r" % driver)
        if schema and not hasattr(schema, 'get'):
            raise TypeError("invalid schema: %r" % schema)
        if crs and not hasattr(crs, 'get'):
            raise TypeError("invalid schema: %r" % crs)
        if encoding and not isinstance(encoding, string_types):
            raise TypeError("invalid encoding: %r" % encoding)
        if layer and not isinstance(layer, tuple(list(string_types) + [int])):
            raise TypeError("invalid name: %r" % layer)
        if vsi:
            if not isinstance(vsi, string_types) or vsi not in ('zip', 'tar', 'gzip'):
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
        self.driver_manager = None
        
        self.path = vsi_path(path, vsi, archive)
        
        if mode == 'w':
            if layer and not isinstance(layer, string_types):
                raise ValueError("in 'r' mode, layer names must be strings")
            if driver == 'GeoJSON':
                if layer is not None:
                    raise ValueError("the GeoJSON format does not have layers")
                self.name = 'OgrGeoJSON'
            # TODO: raise ValueError as above for other single-layer formats.
            else:
                self.name = layer or os.path.basename(os.path.splitext(path)[0])
        else:
            if layer in (0, None):
                self.name = 0
            else:
                self.name = layer or os.path.basename(os.path.splitext(path)[0])
        
        self.mode = mode
        
        if self.mode == 'w':
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
            
            if crs:
                if 'init' in crs or 'proj' in crs:
                    self._crs = crs
                else:
                    raise CRSError("crs lacks init or proj parameter")
        
        if not self.driver_manager and driver_count() == 0:
            # create a local manager and enter
            self.driver_manager = DriverManager()
            self.driver_manager.__enter__()

        if self.mode == "r":
            self.encoding = encoding
            self.session = Session()
            self.session.start(self)
            
            # If encoding param is None, we'll use what the session
            # suggests.
            self.encoding = encoding or self.session.get_fileencoding().lower()

        elif self.mode in ("a", "w"):
            self.encoding = encoding
            self.session = WritingSession()
            self.session.start(self, **kwargs)
            self.encoding = encoding or self.session.get_fileencoding().lower()

        if self.session:
            self.guard_driver_mode()
        
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
        if self._crs is None and self.mode in ("a", "r") and self.session:
            self._crs = self.session.get_crs()
        return self._crs

    @property
    def meta(self):
        """Returns a mapping with the driver, schema, and crs properties."""
        return {
            'driver': self.driver, 
            'schema': self.schema, 
            'crs': self.crs }

    def filter(self, bbox=None):
        """Returns an iterator over records, but filtered by a test for
        spatial intersection with the provided ``bbox``, a (minx, miny,
        maxx, maxy) tuple."""
        if self.closed:
            raise ValueError("I/O operation on closed collection")
        elif self.mode != 'r':
            raise IOError("collection not open for reading")
        self.iterator = Iterator(self, bbox)
        return self.iterator

    def __iter__(self):
        """Returns an iterator over records."""
        return self.filter()

    def __next__(self):
        """Returns next record from iterator."""
        if not self.iterator:
            iter(self)
        return next(self.iterator)

    next = __next__

    def writerecords(self, records):
        """Stages multiple records for writing to disk."""
        if self.closed:
            raise ValueError("I/O operation on closed collection")
        if self.mode not in ('a', 'w'):
            raise IOError("collection not open for writing")
        self.session.writerecs(records, self)
        self._len = self.session.get_length()
        self._bounds = self.session.get_extent()

    def write(self, record):
        """Stages a record for writing to disk."""
        self.writerecords([record])

    def validate_record(self, record):
        """Compares the record to the collection's schema.

        Returns ``True`` if the record matches, else ``False``.
        """
        # Currently we only compare keys of properties, not the types of
        # values.
        return set(record['properties'].keys()
            ) == set(self.schema['properties'].keys()
            ) and self.validate_record_geometry(record)

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
            return (record['geometry']['type'] ==
                self.schema['geometry'].lstrip("3D "))

    def __len__(self):
        if self._len <= 0 and self.session is not None:
            self._len = self.session.get_length()
        return self._len

    @property
    def bounds(self):
        """Returns (minx, miny, maxx, maxy)."""
        if self._bounds is None and self.session is not None:
            self._bounds = self.session.get_extent()
        return self._bounds

    def flush(self):
        """Flush the buffer."""
        if self.session is not None and self.session.get_length() > 0:
            self.session.sync(self)
            new_len = self.session.get_length()
            self._len = new_len > self._len and new_len or self._len
            self._bounds = self.session.get_extent()

    def close(self):
        """In append or write mode, flushes data to disk, then ends
        access."""
        if self.session is not None: 
            if self.mode in ('a', 'w'):
                self.flush()
            self.session.stop()
            self.session = None
            self.iterator = None
        if self.driver_manager:
            self.driver_manager.__exit__()

    @property
    def closed(self):
        """``False`` if data can be accessed, otherwise ``True``."""
        return self.session is None

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __del__(self):
        # Note: you can't count on this being called. Call close() explicitly
        # or use the context manager protocol ("with").
        self.__exit__(None, None, None)


def vsi_path(path, vsi=None, archive=None):
    # If a VSF and archive file are specified, we convert the path to
    # an OGR VSI path (see cpl_vsi.h).
    if vsi:
        if archive:
            result = "/vsi%s/%s%s" % (vsi, archive, path)
        else:
            result = "/vsi%s/%s" % (vsi, path)
    else:
        result = path
    return result


# Here is the list of available drivers as (name, modes) tuples. Currently,
# we only expose the defaults (excepting FileGDB). We also don't expose
# the CSV or GeoJSON drivers. Use Python's csv and json modules instead.
# Might still exclude a few more of these after making a pass through the
# entries for each at http://www.gdal.org/ogr/ogr_formats.html to screen
# out the multi-layer formats.

supported_drivers = dict([
#OGR Vector Formats
#Format Name 	Code 	Creation 	Georeferencing 	Compiled by default
#Aeronav FAA files 	AeronavFAA 	No 	Yes 	Yes
    ("AeronavFAA", "r"),
#ESRI ArcObjects 	ArcObjects 	No 	Yes 	No, needs ESRI ArcObjects
#Arc/Info Binary Coverage 	AVCBin 	No 	Yes 	Yes
# multi-layer
#   ("AVCBin", "r"),
#Arc/Info .E00 (ASCII) Coverage 	AVCE00 	No 	Yes 	Yes
# multi-layer
#    ("AVCE00", "r"),
#Arc/Info Generate 	ARCGEN 	No 	No 	Yes
    ("ARCGEN", "r"),
#Atlas BNA 	BNA 	Yes 	No 	Yes
    ("BNA", "raw"),
#AutoCAD DWG 	DWG 	No 	No 	No
#AutoCAD DXF 	DXF 	Yes 	No 	Yes
    ("DXF", "raw"),
#Comma Separated Value (.csv) 	CSV 	Yes 	No 	Yes
#CouchDB / GeoCouch 	CouchDB 	Yes 	Yes 	No, needs libcurl
#DODS/OPeNDAP 	DODS 	No 	Yes 	No, needs libdap
#EDIGEO 	EDIGEO 	No 	Yes 	Yes
# multi-layer? Hard to tell from the OGR docs
#   ("EDIGEO", "r"),
#ElasticSearch 	ElasticSearch 	Yes (write-only) 	- 	No, needs libcurl
#ESRI FileGDB 	FileGDB 	Yes 	Yes 	No, needs FileGDB API library
# multi-layer
    ("FileGDB", "raw"),
#ESRI Personal GeoDatabase 	PGeo 	No 	Yes 	No, needs ODBC library
#ESRI ArcSDE 	SDE 	No 	Yes 	No, needs ESRI SDE
#ESRI Shapefile 	ESRI Shapefile 	Yes 	Yes 	Yes
    ("ESRI Shapefile", "raw"),
#FMEObjects Gateway 	FMEObjects Gateway 	No 	Yes 	No, needs FME
#GeoJSON 	GeoJSON 	Yes 	Yes 	Yes
    ("GeoJSON", "rw"),
#Géoconcept Export 	Geoconcept 	Yes 	Yes 	Yes
# multi-layers
#   ("Geoconcept", "raw"),
#Geomedia .mdb 	Geomedia 	No 	No 	No, needs ODBC library
#GeoRSS 	GeoRSS 	Yes 	Yes 	Yes (read support needs libexpat)
#Google Fusion Tables 	GFT 	Yes 	Yes 	No, needs libcurl
#GML 	GML 	Yes 	Yes 	Yes (read support needs Xerces or libexpat)
#GMT 	GMT 	Yes 	Yes 	Yes
    ("GMT", "raw"),
#GPSBabel 	GPSBabel 	Yes 	Yes 	Yes (needs GPSBabel and GPX driver)
#GPX 	GPX 	Yes 	Yes 	Yes (read support needs libexpat)
#GRASS 	GRASS 	No 	Yes 	No, needs libgrass
#GPSTrackMaker (.gtm, .gtz) 	GPSTrackMaker 	Yes 	Yes 	Yes
    ("GPSTrackMaker", "raw"),
#Hydrographic Transfer Format 	HTF 	No 	Yes 	Yes
# TODO: Fiona is not ready for multi-layer formats: ("HTF", "r"),
#Idrisi Vector (.VCT) 	Idrisi 	No 	Yes 	Yes
    ("Idrisi", "r"),
#Informix DataBlade 	IDB 	Yes 	Yes 	No, needs Informix DataBlade
#INTERLIS 	"Interlis 1" and "Interlis 2" 	Yes 	Yes 	No, needs Xerces (INTERLIS model reading needs ili2c.jar)
#INGRES 	INGRES 	Yes 	No 	No, needs INGRESS
#KML 	KML 	Yes 	Yes 	Yes (read support needs libexpat)
#LIBKML 	LIBKML 	Yes 	Yes 	No, needs libkml
#Mapinfo File 	MapInfo File 	Yes 	Yes 	Yes
    ("MapInfo File", "raw"),
#Microstation DGN 	DGN 	Yes 	No 	Yes
    ("DGN", "raw"),
#Access MDB (PGeo and Geomedia capable) 	MDB 	No 	Yes 	No, needs JDK/JRE
#Memory 	Memory 	Yes 	Yes 	Yes
#MySQL 	MySQL 	No 	Yes 	No, needs MySQL library
#NAS - ALKIS 	NAS 	No 	Yes 	No, needs Xerces
#Oracle Spatial 	OCI 	Yes 	Yes 	No, needs OCI library
#ODBC 	ODBC 	No 	Yes 	No, needs ODBC library
#MS SQL Spatial 	MSSQLSpatial 	Yes 	Yes 	No, needs ODBC library
#Open Document Spreadsheet 	ODS 	Yes 	No 	No, needs libexpat
#OGDI Vectors (VPF, VMAP, DCW) 	OGDI 	No 	Yes 	No, needs OGDI library
#OpenAir 	OpenAir 	No 	Yes 	Yes
# multi-layer
#   ("OpenAir", "r"),
#PCI Geomatics Database File 	PCIDSK 	No 	No 	Yes, using internal PCIDSK SDK (from GDAL 1.7.0)
    ("PCIDSK", "r"),
#PDS 	PDS 	No 	Yes 	Yes
    ("PDS", "r"),
#PGDump 	PostgreSQL SQL dump 	Yes 	Yes 	Yes
#PostgreSQL/PostGIS 	PostgreSQL/PostGIS 	Yes 	Yes 	No, needs PostgreSQL client library (libpq)
#EPIInfo .REC 	REC 	No 	No 	Yes
#S-57 (ENC) 	S57 	No 	Yes 	Yes
# multi-layer
#   ("S57", "r"),
#SDTS 	SDTS 	No 	Yes 	Yes
# multi-layer
#   ("SDTS", "r"),
#SEG-P1 / UKOOA P1/90 	SEGUKOOA 	No 	Yes 	Yes
# multi-layers
#   ("SEGUKOOA", "r"),
#SEG-Y 	SEGY 	No 	No 	Yes
    ("SEGY", "r"),
#Norwegian SOSI Standard 	SOSI 	No 	Yes 	No, needs FYBA library
#SQLite/SpatiaLite 	SQLite 	Yes 	Yes 	No, needs libsqlite3 or libspatialite
#SUA 	SUA 	No 	Yes 	Yes
    ("SUA", "r"),
#SVG 	SVG 	No 	Yes 	No, needs libexpat
#UK .NTF 	UK. NTF 	No 	Yes 	Yes
# multi-layer
#   ("UK. NTF", "r"),
#U.S. Census TIGER/Line 	TIGER 	No 	Yes 	Yes
# multi-layer
#   ("TIGER", "r"),
#VFK data 	VFK 	No 	Yes 	Yes
# multi-layer
#   ("VFK", "r"),
#VRT - Virtual Datasource 	VRT 	No 	Yes 	Yes
# multi-layer
#   ("VRT", "r"),
#OGC WFS (Web Feature Service) 	WFS 	Yes 	Yes 	No, needs libcurl
#MS Excel format 	XLS 	No 	No 	No, needs libfreexl
#Office Open XML spreadsheet 	XLSX 	Yes 	No 	No, needs libexpat
#X-Plane/Flighgear aeronautical data 	XPLANE 	No 	Yes 	Yes
# multi-layer
#   ("XPLANE", "r") 
])

