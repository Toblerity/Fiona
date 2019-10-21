# Coordinate system and transform API functions.

cdef extern from "ogr_srs_api.h":

    ctypedef void * OGRSpatialReferenceH

    void    OSRCleanup ()
    OGRSpatialReferenceH  OSRClone (OGRSpatialReferenceH srs)
    int     OSRExportToProj4 (OGRSpatialReferenceH srs, char **params)
    int     OSRExportToWkt (OGRSpatialReferenceH srs, char **params)
    int     OSRImportFromEPSG (OGRSpatialReferenceH srs, int code)
    int     OSRImportFromProj4 (OGRSpatialReferenceH srs, char *proj)
    int     OSRSetFromUserInput (OGRSpatialReferenceH srs, char *input)
    int     OSRAutoIdentifyEPSG (OGRSpatialReferenceH srs)
    const char * OSRGetAuthorityName (OGRSpatialReferenceH srs, const char *key)
    const char * OSRGetAuthorityCode (OGRSpatialReferenceH srs, const char *key)
    OGRSpatialReferenceH  OSRNewSpatialReference (char *wkt)
    void    OSRRelease (OGRSpatialReferenceH srs)
    void *  OCTNewCoordinateTransformation (OGRSpatialReferenceH source, OGRSpatialReferenceH dest)
    void    OCTDestroyCoordinateTransformation (void *source)
    int     OCTTransform (void *ct, int nCount, double *x, double *y, double *z)
