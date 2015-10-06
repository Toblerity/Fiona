# -*- coding: utf-8 -*-

from fiona._drivers import GDALEnv


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
    ("OpenFileGDB", "r"),
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
#GeoPackage	GPKG	Yes	Yes	No, needs libsqlite3
    ("GPKG", "rw"),
#GeoRSS 	GeoRSS 	Yes 	Yes 	Yes (read support needs libexpat)
#Google Fusion Tables 	GFT 	Yes 	Yes 	No, needs libcurl
#GML 	GML 	Yes 	Yes 	Yes (read support needs Xerces or libexpat)
#GMT 	GMT 	Yes 	Yes 	Yes
    ("GMT", "raw"),
#GPSBabel 	GPSBabel 	Yes 	Yes 	Yes (needs GPSBabel and GPX driver)
#GPX 	GPX 	Yes 	Yes 	Yes (read support needs libexpat)
    ("GPX", "raw"),
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


# Removes drivers in the supported_drivers dictionary that the   
# machine's installation of OGR due to how it is compiled.
# OGR may not have optional libararies compiled or installed.
def _filter_supported_drivers():
    global supported_drivers

    gdalenv = GDALEnv()
    ogrdrv_names = gdalenv.start().drivers().keys()
    supported_drivers_copy = supported_drivers.copy()

    for drv in supported_drivers.keys():
        if drv not in ogrdrv_names:
            del supported_drivers_copy[drv]

    gdalenv.stop()

    supported_drivers = supported_drivers_copy

_filter_supported_drivers()
