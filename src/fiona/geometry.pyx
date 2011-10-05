# A Python data structure that provides the Python geo interface

from array import array

cimport ograpi

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
    def __init__(self, type, parts=None):
        """Type is one of the GeoJSON types ('Point', 'LineString', etc)"""
        self.type = type
        self.parts = parts or []
        
    @property
    def coordinates(self):
        # Zip coordinate arrays 
        if len(self.parts) == 0:
            return None
        elif len(self.parts) == 1:
            part = self.parts[0]
            if len(part.x) == len(part.y) == 1 and self.type == 'Point':
                return (part.x[0], part.y[0])
            else:
                return zip(part.x, part.y)
        else:
            value = []
            for part in self.parts:
                value.append(zip(part.x, part.y))
            return value
        
    @property
    def __geo_interface__(self):
        return {'type': self.type, 'coordinates': self.coordinates}


def test_line():
    # Hex-encoded LineString (0 0, 1 1)
    wkb = "01020000000200000000000000000000000000000000000000000000000000f03f000000000000f03f".decode('hex')
    cdef unsigned char *buffer = wkb
    cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(2)
    ograpi.OGR_G_ImportFromWkb(cogr_geometry, buffer, len(wkb))
    result = geometry(cogr_geometry)
    ograpi.OGR_G_DestroyGeometry(cogr_geometry)
    return result

cdef geometry(void *cogr_geometry):
    cdef unsigned char *buffer = ograpi.OGR_G_ExportToJson(cogr_geometry)
    cdef bytes result = buffer
    ograpi.CPLFree(buffer)
    return result

