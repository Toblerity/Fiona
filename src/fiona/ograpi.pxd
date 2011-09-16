# Copyright (c) 2007, Sean C. Gillies
# All rights reserved.
# See ../LICENSE.txt

cdef extern from "ogr_api.h":
    char *  OGR_Dr_GetName (void *driver)
    void    OGR_DS_Destroy (void *datasource)
    void *  OGR_DS_GetDriver (void *layer_defn)
    void *  OGR_DS_GetLayerByName (void *datasource, char *name)
    int     OGR_DS_GetLayerCount (void *datasource)
    void *  OGR_DS_GetLayer (void *datasource, int n)
    void    OGR_F_Destroy (void *feature)
    long    OGR_F_GetFID (void *feature)
    double  OGR_F_GetFieldAsDouble (void *feature, int n)
    int     OGR_F_GetFieldAsInteger (void *feature, int n)
    char *  OGR_F_GetFieldAsString (void *feature, int n)
    void *  OGR_F_GetGeometryRef (void *feature)
    int     OGR_FD_GetFieldCount (void *featuredefn)
    void *  OGR_FD_GetFieldDefn (void *featuredefn, int n)
    char *  OGR_FD_GetName (void *layer_defn)
    char *  OGR_Fld_GetNameRef (void *fielddefn)
    int     OGR_Fld_GetType (void *fielddefn)
    void    OGR_G_DestroyGeometry (void *geometry) 
    void    OGR_G_ExportToWkb (void *geometry, int endianness, char *buffer)
    int     OGR_G_WkbSize (void *geometry)
    void *  OGR_L_GetFeature (void *layer, int n)
    int     OGR_L_GetFeatureCount (void *layer, int m)
    void *  OGR_L_GetLayerDefn (void *layer)
    void *  OGR_L_GetNextFeature (void *layer)
    void *  OGR_L_GetSpatialFilter (void *layer)
    void    OGR_L_ResetReading (void *layer)
    void    OGR_L_SetSpatialFilter (void *layer, void *geometry)
    void    OGR_L_SetSpatialFilterRect (
                void *layer, double minx, double miny, double maxx, double maxy
                )
    void *  OGROpen (char *path, int mode, void *x)
    void *  OGROpenShared (char *path, int mode, void *x)
    int     OGRReleaseDataSource (void *datasource)

cdef extern from "cpl_error.h":
    void    CPLSetErrorHandler (void *handler)
    void *  CPLQuietErrorHandler

