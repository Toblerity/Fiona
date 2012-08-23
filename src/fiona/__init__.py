# -*- coding: utf-8 -*-

"""
Fiona is OGR's neater API – sleek and elegant on the outside,
indomitable power on the inside.

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

  >>> from fiona import collection
  >>> with collection("docs/data/test_uk.shp", "r") as input:
  ...     schema = input.schema.copy()
  ...     schema['geometry'] = 'Point'
  ...     with collection(
  ...             "points.shp", "w", "ESRI Shapefile",
  ...             schema=schema, crs=input.crs
  ...             ) as output:
  ...         for f in input.filter(
  ...                 bbox=(-5.0, 55.0, 0.0, 60.0)
  ...                 ):
  ...             value = f['geometry']['coordinates'][0][0]
  ...             f['geometry'] = dict(
  ...                 type='Point', coordinates=value)
  ...             output.write(f)

Because Fiona collections are context managers, they are closed and (in
writing modes) flush contents to disk when their ``with`` blocks end.
"""

__version__ = "0.8.1"

import os

from fiona.collection import Collection


def collection(path, mode='r', driver=None, schema=None, crs=None):
    
    """Open file at ``path`` in ``mode`` "r" (read), "a" (append), or
    "w" (write) and return a ``Collection`` object.
    
    In write mode, a driver name such as "ESRI Shapefile" or "GPX" (see
    OGR docs or ``ogr2ogr --help`` on the command line) and a schema
    mapping such as:
    
      {'geometry': 'Point', 'properties': { 'class': 'int', 'label':
      'str', 'value': 'float'}}
    
    must be provided. A coordinate reference system for collections in
    write mode can be defined by the ``crs`` parameter. It takes Proj4
    style mappings like
    
      {'proj': 'longlat', 'ellps': 'WGS84', 'datum': 'WGS84', 
       'no_defs': True}
    
    """
    if mode in ('a', 'r'):
        if not os.path.exists(path):
            raise OSError("Nonexistent path '%s'" % path)
        if not os.path.isfile(path):
            raise ValueError("Path must be a file")
        c = Collection(path, mode)
    elif mode == 'w':
        dirname = os.path.dirname(path) or "."
        if not os.path.exists(dirname):
            raise OSError("Nonexistent path '%s'" % path)
        if not driver:
            raise ValueError("An OGR driver name must be specified")
        if not schema:
            raise ValueError("A collection schema must be specified")
        c = Collection(path, mode, driver, schema, crs)
    else:
        raise ValueError("Invalid mode: %s" % mode)
    return c

# Here is the list of available drivers as (name, modes) tuples. Currently,
# we only expose the defaults (excepting FileGDB). We also don't expose
# the CSV or GeoJSON drivers. Use Python's csv and json modules instead.
# Might still exclude a few more of these after making a pass through the
# entries for each at http://www.gdal.org/ogr/ogr_formats.html to screen
# out the multi-layer formats.

drivers = [
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
#   ("FileGDB", "raw?"),
#ESRI Personal GeoDatabase 	PGeo 	No 	Yes 	No, needs ODBC library
#ESRI ArcSDE 	SDE 	No 	Yes 	No, needs ESRI SDE
#ESRI Shapefile 	ESRI Shapefile 	Yes 	Yes 	Yes
    ("ESRI Shapefile", "raw"),
#FMEObjects Gateway 	FMEObjects Gateway 	No 	Yes 	No, needs FME
#GeoJSON 	GeoJSON 	Yes 	Yes 	Yes
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
]

