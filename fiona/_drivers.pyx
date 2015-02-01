# The GDAL and OGR driver registry.
# GDAL driver management.

import os
import os.path
import logging
import sys

from six import string_types


cdef extern from "cpl_conv.h":
    void    CPLFree (void *ptr)
    void    CPLSetThreadLocalConfigOption (char *key, char *val)
    const char * CPLGetConfigOption ( const char *key, const char *default)


cdef extern from "cpl_error.h":
    void CPLSetErrorHandler (void *handler)


cdef extern from "gdal.h":
    void GDALAllRegister()
    void GDALDestroyDriverManager()
    int GDALGetDriverCount()
    void * GDALGetDriver(int i)
    const char * GDALGetDriverShortName(void *driver)
    const char * GDALGetDriverLongName(void *driver)


cdef extern from "ogr_api.h":
    void OGRRegisterDriver(void *driver)
    void OGRDeregisterDriver(void *driver)
    void OGRRegisterAll()
    void OGRCleanupAll()
    int OGRGetDriverCount()
    void * OGRGetDriver(int i)
    void * OGRGetDriverByName(const char *name)
    const char * OGR_Dr_GetName(void *driver)


log = logging.getLogger('Fiona')
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
log.addHandler(NullHandler())


level_map = {
    0: 0,
    1: logging.DEBUG,
    2: logging.WARNING,
    3: logging.ERROR,
    4: logging.CRITICAL }

code_map = {
    0: 'CPLE_None',
    1: 'CPLE_AppDefined',
    2: 'CPLE_OutOfMemory',
    3: 'CPLE_FileIO',
    4: 'CPLE_OpenFailed',
    5: 'CPLE_IllegalArg',
    6: 'CPLE_NotSupported',
    7: 'CPLE_AssertionFailed',
    8: 'CPLE_NoWriteAccess',
    9: 'CPLE_UserInterrupt',
    10: 'CPLE_ObjectNull'
}

cdef void * errorHandler(int eErrClass, int err_no, char *msg):
    log.log(level_map[eErrClass], "%s in %s", code_map[err_no], msg)


def driver_count():
    return OGRGetDriverCount()


cdef class GDALEnv(object):

    cdef public object options

    def __init__(self, **options):
        self.options = options.copy()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        self.stop()

    def start(self):
        cdef const char *key_c = NULL
        cdef const char *val_c = NULL

        if GDALGetDriverCount() == 0:
            GDALAllRegister()
        if OGRGetDriverCount() == 0:
            OGRRegisterAll()
        CPLSetErrorHandler(<void *>errorHandler)
        if OGRGetDriverCount() == 0:
            raise ValueError("Drivers not registered")

        if 'GDAL_DATA' not in os.environ:
            whl_datadir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "gdal_data"))
            share_datadir = os.path.join(sys.prefix, 'share/gdal')
            if os.path.exists(os.path.join(whl_datadir, 'pcs.csv')):
                os.environ['GDAL_DATA'] = whl_datadir
            elif os.path.exists(os.path.join(share_datadir, 'pcs.csv')):
                os.environ['GDAL_DATA'] = share_datadir
        if 'PROJ_LIB' not in os.environ:
            whl_datadir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "proj_data"))
            os.environ['PROJ_LIB'] = whl_datadir

        for key, val in self.options.items():
            key_b = key.upper().encode('utf-8')
            key_c = key_b
            if isinstance(val, string_types):
                val_b = val.encode('utf-8')
            else:
                val_b = ('ON' if val else 'OFF').encode('utf-8')
            val_c = val_b
            CPLSetThreadLocalConfigOption(key_c, val_c)
            log.debug("Option %s=%s", key, CPLGetConfigOption(key_c, NULL))
        return self

    def stop(self):
        cdef const char *key_c = NULL
        for key in self.options:
            key_b = key.upper().encode('utf-8')
            key_c = key_b
            CPLSetThreadLocalConfigOption(key_c, NULL)
        CPLSetErrorHandler(NULL)

    def drivers(self):
        cdef void *drv = NULL
        cdef char *key = NULL
        cdef char *val = NULL
        cdef int i
        result = {}
        for i in range(OGRGetDriverCount()):
            drv = OGRGetDriver(i)
            key = OGR_Dr_GetName(drv)
            key_b = key
            val = OGR_Dr_GetName(drv)
            val_b = val
            result[key_b.decode('utf-8')] = val_b.decode('utf-8')
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
