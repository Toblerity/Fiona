# Extension classes and functions

from fiona cimport ograpi

geometryTypes = [
    'Unknown', 
    'Point', 'LineString', 'Polygon', 'MultiPoint', 
    'MultiLineString', 'MultiPolygon', 'GeometryCollection',
    'None', 'LinearRing', 
    'Point25D', 'LineString25D', 'Polygon25D', 'MultiPoint25D', 
    'MultiLineString25D', 'MultiPolygon25D', 'GeometryCollection25D'
    ]

cdef void * _createOgrGeomFromWKB(object wkb):
    """Make an OGR geometry from a WKB string"""
    geom_type = bytearray(wkb)[1]
    cdef unsigned char *buffer = wkb
    cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(geom_type)
    ograpi.OGR_G_ImportFromWkb(cogr_geometry, buffer, len(wkb))
    return cogr_geometry

cdef _deleteOgrGeom(void *cogr_geometry):
    """Delete an OGR geometry"""
    ograpi.OGR_G_DestroyGeometry(cogr_geometry)

cdef class Builder:
    """Builds Fiona geometries from an OGR geometry handle."""
    cdef void *geom
    cdef object code
    cdef object typename
    cdef object ndims
    cdef object Geometry
    cdef object CoordSequence

    cdef _buildCoords(self, void *geom):
        # Build a coordinate sequence
        cdef int i
        npoints = ograpi.OGR_G_GetPointCount(geom)
        cs = self.CoordSequence(*[[0.0]*npoints]*self.ndims)
        for i in range(npoints):
            cs.x[i] = ograpi.OGR_G_GetX(geom, i)
            cs.y[i] = ograpi.OGR_G_GetY(geom, i)
        if self.ndims > 2:
            for i in range(npoints):
                cs.z[i] = ograpi.OGR_G_GetZ(geom, i)
        return cs
    cpdef _buildPoint(self):
        cs = self._buildCoords(self.geom)
        return self.Geometry('Point', [cs])
    cpdef _buildLineString(self):
        cs = self._buildCoords(self.geom)
        return self.Geometry('LineString', [cs])
    # TODO: polygon
    
    cdef _buildParts(self, void *geom):
        # Build a list of geometry parts
        cdef int j
        cdef void *part
        parts = []
        for j in range(ograpi.OGR_G_GetGeometryCount(geom)):
            part = ograpi.OGR_G_GetGeometryRef(geom, j)
            parts.append(Builder().build(self.Geometry, self.CoordSequence, part))
        return parts
    cpdef _buildMultiPoint(self):
        return self.Geometry('MultiPoint', parts=self._buildParts(self.geom))
    # TODO: other multis

    cdef build(self, object geom_klass, object cseq_klass, void *geom):
        # The only method anyone needs to call
        self.code = ograpi.OGR_G_GetGeometryType(geom)
        self.typename = geometryTypes[self.code]
        self.ndims = ograpi.OGR_G_GetCoordinateDimension(geom)
        self.geom = geom
        self.Geometry = geom_klass
        self.CoordSequence = cseq_klass
        return getattr(self, '_build' + self.typename)()

    cpdef build_wkb(self, object geom_klass, object cseq_klass, object wkb):
        # The only method anyone needs to call
        cdef object data = wkb
        cdef void *cogr_geometry = _createOgrGeomFromWKB(data)
        result = self.build(geom_klass, cseq_klass, cogr_geometry)
        _deleteOgrGeom(cogr_geometry)
        return result

#cdef geometry(void *geom):
#    """Factory for Fiona geometries"""
#    return Builder().build(geom)


