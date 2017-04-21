# Copyright (c) 2007, Sean C. Gillies
# All rights reserved.
# See ../LICENSE.txt

cdef extern from "gdal.h":
    char * GDALVersionInfo (char *pszRequest)
    void * GDALGetDriverByName(const char * pszName)
    void * GDALOpenEx(const char * pszFilename,
                      unsigned int nOpenFlags,
                      const char ** papszAllowedDrivers,
                      const char ** papszOpenOptions,
                      const char *const *papszSibling1Files
                      )
    int GDAL_OF_UPDATE
    int GDAL_OF_READONLY
    int GDAL_OF_VECTOR
    int GDAL_OF_VERBOSE_ERROR
    int GDALDatasetGetLayerCount(void * hds)
    void * GDALDatasetGetLayer(void * hDS, int iLayer)
    void * GDALDatasetGetLayerByName(void * hDS, char * pszName)
    void GDALClose(void * hDS)
    void * GDALGetDatasetDriver(void * hDataset)
    void * GDALCreate(void * hDriver,
                      const char * pszFilename,
                      int nXSize,
                      int     nYSize,
                      int     nBands,
                      GDALDataType eBandType,
                      char ** papszOptions)
    void * GDALDatasetCreateLayer(void * hDS,
                                  const char * pszName,
                                  void * hSpatialRef,
                                  int eType,
                                  char ** papszOptions)
    int GDALDatasetDeleteLayer(void * hDS, int iLayer)
    void GDALFlushCache(void * hDS)
    char * GDALGetDriverShortName(void * hDriver)
    char * GDALGetDatasetDriver (void * hDataset)
    int GDALDeleteDataset(void * hDriver, const char * pszFilename)


    ctypedef enum GDALDataType:
        GDT_Unknown
        GDT_Byte
        GDT_UInt16
        GDT_Int16
        GDT_UInt32
        GDT_Int32
        GDT_Float32
        GDT_Float64
        GDT_CInt16
        GDT_CInt32
        GDT_CFloat32
        GDT_CFloat64
        GDT_TypeCount

cdef extern from "gdal_version.h":
    int    GDAL_COMPUTE_VERSION(int maj, int min, int rev)

cdef extern from "cpl_conv.h":
    void *  CPLMalloc (size_t)
    void    CPLFree (void *ptr)
    void    CPLSetThreadLocalConfigOption (char *key, char *val)
    const char *CPLGetConfigOption (char *, char *)


cdef extern from "cpl_string.h":
    char ** CSLSetNameValue (char **list, const char *name, const char *value)
    void CSLDestroy (char **list)
    char ** CSLAddString(char **list, const char *string)


cdef extern from "cpl_vsi.h":
    ctypedef struct VSILFILE:
        pass
    int VSIFCloseL (VSILFILE *)
    VSILFILE * VSIFileFromMemBuffer (const char * filename,
                                     unsigned char * data,
                                     int data_len,
                                     int take_ownership)
    int VSIUnlink (const char * pathname)


cdef extern from "ogr_core.h":

    ctypedef int OGRErr

    ctypedef struct OGREnvelope:
        double MinX
        double MaxX
        double MinY
        double MaxY

    char *  OGRGeometryTypeToName(int)


cdef extern from "ogr_srs_api.h":

    ctypedef void * OGRSpatialReferenceH

    void    OSRCleanup ()
    OGRSpatialReferenceH  OSRClone (OGRSpatialReferenceH srs)
    int     OSRExportToProj4 (OGRSpatialReferenceH srs, char **params)
    int     OSRExportToWkt (OGRSpatialReferenceH srs, char **params)
    int     OSRImportFromEPSG (OGRSpatialReferenceH, int code)
    int     OSRImportFromProj4 (OGRSpatialReferenceH srs, const char *proj)
    int     OSRSetFromUserInput (OGRSpatialReferenceH srs, const char *input)
    int     OSRAutoIdentifyEPSG (OGRSpatialReferenceH srs)
    int     OSRFixup(OGRSpatialReferenceH srs)
    const char * OSRGetAuthorityName (OGRSpatialReferenceH srs, const char *key)
    const char * OSRGetAuthorityCode (OGRSpatialReferenceH srs, const char *key)
    OGRSpatialReferenceH  OSRNewSpatialReference (char *wkt)
    void    OSRRelease (OGRSpatialReferenceH srs)
    void *  OCTNewCoordinateTransformation (OGRSpatialReferenceH source, OGRSpatialReferenceH dest)
    void    OCTDestroyCoordinateTransformation (void *source)
    int     OCTTransform (void *ct, int nCount, double *x, double *y, double *z)

cdef extern from "ogr_api.h":

    char *  OGR_Dr_GetName (void *driver)
    void *  OGR_Dr_CreateDataSource (void *driver, const char *path, char **options)
    int     OGR_Dr_DeleteDataSource (void *driver, char *)
    void *  OGR_Dr_Open (void *driver, const char *path, int bupdate)
    int     OGR_Dr_TestCapability (void *driver, const char *)
    void *  OGR_F_Create (void *featuredefn)
    void    OGR_F_Destroy (void *feature)
    long    OGR_F_GetFID (void *feature)
    int     OGR_F_IsFieldSet (void *feature, int n)
    int     OGR_F_GetFieldAsDateTime (void *feature, int n, int *y, int *m, int *d, int *h, int *m, int *s, int *z)
    double  OGR_F_GetFieldAsDouble (void *feature, int n)
    int     OGR_F_GetFieldAsInteger (void *feature, int n)
    char *  OGR_F_GetFieldAsString (void *feature, int n)
    int     OGR_F_GetFieldCount (void *feature)
    void *  OGR_F_GetFieldDefnRef (void *feature, int n)
    int     OGR_F_GetFieldIndex (void *feature, char *name)
    void *  OGR_F_GetGeometryRef (void *feature)
    void    OGR_F_SetFieldDateTime (void *feature, int n, int y, int m, int d, int hh, int mm, int ss, int tz)
    void    OGR_F_SetFieldDouble (void *feature, int n, double value)
    void    OGR_F_SetFieldInteger (void *feature, int n, int value)
    void    OGR_F_SetFieldString (void *feature, int n, char *value)
    int     OGR_F_SetGeometryDirectly (void *feature, void *geometry)
    void *  OGR_FD_Create (char *name)
    int     OGR_FD_GetFieldCount (void *featuredefn)
    void *  OGR_FD_GetFieldDefn (void *featuredefn, int n)
    int     OGR_FD_GetGeomType (void *featuredefn)
    char *  OGR_FD_GetName (void *featuredefn)
    void *  OGR_Fld_Create (char *name, int fieldtype)
    void    OGR_Fld_Destroy (void *fielddefn)
    char *  OGR_Fld_GetNameRef (void *fielddefn)
    int     OGR_Fld_GetPrecision (void *fielddefn)
    int     OGR_Fld_GetType (void *fielddefn)
    int     OGR_Fld_GetWidth (void *fielddefn)
    void    OGR_Fld_Set (void *fielddefn, char *name, int fieldtype, int width, int precision, int justification)
    void    OGR_Fld_SetPrecision (void *fielddefn, int n)
    void    OGR_Fld_SetWidth (void *fielddefn, int n)
    OGRErr  OGR_G_AddGeometryDirectly (void *geometry, void *part)
    void    OGR_G_AddPoint (void *geometry, double x, double y, double z)
    void    OGR_G_AddPoint_2D (void *geometry, double x, double y)
    void    OGR_G_CloseRings (void *geometry)
    void *  OGR_G_CreateGeometry (int wkbtypecode)
    void    OGR_G_DestroyGeometry (void *geometry)
    unsigned char *  OGR_G_ExportToJson (void *geometry)
    void    OGR_G_ExportToWkb (void *geometry, int endianness, char *buffer)
    int     OGR_G_GetCoordinateDimension (void *geometry)
    int     OGR_G_GetGeometryCount (void *geometry)
    unsigned char *  OGR_G_GetGeometryName (void *geometry)
    int     OGR_G_GetGeometryType (void *geometry)
    void *  OGR_G_GetGeometryRef (void *geometry, int n)
    int     OGR_G_GetPointCount (void *geometry)
    double  OGR_G_GetX (void *geometry, int n)
    double  OGR_G_GetY (void *geometry, int n)
    double  OGR_G_GetZ (void *geometry, int n)
    void    OGR_G_ImportFromWkb (void *geometry, unsigned char *bytes, int nbytes)
    int     OGR_G_WkbSize (void *geometry)
    OGRErr  OGR_L_CreateFeature (void *layer, void *feature)
    int     OGR_L_CreateField (void *layer, void *fielddefn, int flexible)
    OGRErr  OGR_L_GetExtent (void *layer, void *extent, int force)
    void *  OGR_L_GetFeature (void *layer, int n)
    int     OGR_L_GetFeatureCount (void *layer, int m)
    void *  OGR_L_GetLayerDefn (void *layer)
    char *  OGR_L_GetName (void *layer)
    void *  OGR_L_GetNextFeature (void *layer)
    void *  OGR_L_GetSpatialFilter (void *layer)
    void *  OGR_L_GetSpatialRef (void *layer)
    void    OGR_L_ResetReading (void *layer)
    void    OGR_L_SetSpatialFilter (void *layer, void *geometry)
    void    OGR_L_SetSpatialFilterRect (
                void *layer, double minx, double miny, double maxx, double maxy
                )
    int     OGR_L_TestCapability (void *layer, char *name)
    void *  OGRGetDriverByName (char *)
    void *  OGROpen (char *path, int mode, void *x)
    void *  OGROpenShared (char *path, int mode, void *x)
    int     OGRReleaseDataSource (void *datasource)
    OGRErr  OGR_L_SetNextByIndex (void *layer, long nIndex)
    long long OGR_F_GetFieldAsInteger64 (void *feature, int n)
    void    OGR_F_SetFieldInteger64 (void *feature, int n, long long value)
