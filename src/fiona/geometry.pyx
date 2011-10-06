# A Python data structure that provides the Python geo interface

from array import array

cimport ograpi

geometryTypes = [
    'Unknown', 
    'Point', 'LineString', 'Polygon', 'MultiPoint', 
    'MultiLineString', 'MultiPolygon', 'GeometryCollection',
    'None', 'LinearRing', 
    'Point25D', 'LineString25D', 'Polygon25D', 'MultiPoint25D', 
    'MultiLineString25D', 'MultiPolygon25D', 'GeometryCollection25D'
    ]

class CoordSequence(object):
    """A trio of coordinate arrays"""
    def __init__(self, x=None, y=None, z=None):
        """Parameters x and y are coordinate value sequences"""
        if x and y:
            assert len(x) == len(y)
            self.x = array('d', x)
            self.y = array('d', y)
            if z:
                assert len(z) == len(x)
                self.z = array('d', z)
        else:
            self.x = array('d', [])
            self.y = array('d', [])
            self.z = array('d', [])

class Geometry(object):
    """A data structure that provides the Python geo interface"""
    # One or more coordinate array parts and a geometry type to distinguish
    # between line strings and multipoints
    def __init__(self, type, sequences=None, parts=None):
        """Type is one of the GeoJSON types ('Point', 'LineString', etc)"""
        self.type = type
        self.sequences = sequences or []
        self.parts = parts or []
    
    @property
    def coordinates(self):
        # TODO: redo this with method dispatching
        if len(self.parts) == 0: # single part geometries
            if len(self.sequences) == 0:
                return None
            elif len(self.sequences) == 1: # points, linestrings
                cs = self.sequences[0]
                if len(cs.x) == len(cs.y) == 1 and self.type == 'Point':
                    return (cs.x[0], cs.y[0])
                else:
                    return zip(cs.x, cs.y)
            else:
                value = []
                for cs in self.sequences:
                    value.append(zip(cs.x, cs.y))
                return value
        else:
            assert self.type == 'MultiPoint'
            value = []
            for part in self.parts:
                cs = part.sequences[0]
                value.extend(zip(cs.x, cs.y))
            return value

    @property
    def __geo_interface__(self):
        return {'type': self.type, 'coordinates': self.coordinates}

cdef class Builder:
    """Builds Fiona geometries from an OGR geometry handle."""
    cdef void *geom
    cdef object code
    cdef object typename
    cdef object ndims
    cdef object nparts
    cdef _buildCoords(self, void *geom):
        cdef int i
        npoints = ograpi.OGR_G_GetPointCount(geom)
        cs = CoordSequence(*[[0.0]*npoints]*self.ndims)
        for i in range(npoints):
            cs.x[i] = ograpi.OGR_G_GetX(geom, i)
            cs.y[i] = ograpi.OGR_G_GetY(geom, i)
        if self.ndims > 2:
            for i in range(npoints):
                cs.z[i] = ograpi.OGR_G_GetZ(geom, i)
        return cs
    cpdef _buildPoint(self):
        cs = self._buildCoords(self.geom)
        return Geometry('Point', [cs])
    cpdef _buildLineString(self):
        cs = self._buildCoords(self.geom)
        return Geometry('LineString', [cs])
    # TODO: polygon
    cpdef _buildMultiPoint(self):
        cdef int j
        cdef void *part
        parts = []
        for j in range(self.nparts):
            part = ograpi.OGR_G_GetGeometryRef(self.geom, j)
            parts.append(Builder().build(part))
        return Geometry('MultiPoint', parts=parts)
    # TODO: other multis
    cdef build(self, void *geom):
        # The only method anyone needs to call
        self.code = ograpi.OGR_G_GetGeometryType(geom)
        self.typename = geometryTypes[self.code]
        self.ndims = ograpi.OGR_G_GetCoordinateDimension(geom)
        self.nparts = ograpi.OGR_G_GetGeometryCount(geom)
        self.geom = geom
        return getattr(self, '_build' + self.typename)()

cdef geometry(void *geom):
    """Factory for Fiona geometries"""
    return Builder().build(geom)

def test_line():
    # Hex-encoded LineString (0 0, 1 1)
    wkb = "01020000000200000000000000000000000000000000000000000000000000f03f000000000000f03f".decode('hex')
    cdef unsigned char *buffer = wkb
    cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(2)
    ograpi.OGR_G_ImportFromWkb(cogr_geometry, buffer, len(wkb))
    result = geometry(cogr_geometry)
    ograpi.OGR_G_DestroyGeometry(cogr_geometry)
    return result

def test_multipoint():
    # Hex-encoded MultiPoint (0 0, 1 1)
    wkb = "0104000000020000000101000000000000000000000000000000000000000101000000000000000000f03f000000000000f03f".decode('hex')
    cdef unsigned char *buffer = wkb
    cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(
                                geometryTypes.index('MultiPoint'))
    ograpi.OGR_G_ImportFromWkb(cogr_geometry, buffer, len(wkb))
    result = geometry(cogr_geometry)
    ograpi.OGR_G_DestroyGeometry(cogr_geometry)
    return result

