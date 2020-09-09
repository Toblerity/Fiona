# Coordinate and geometry transformations.

from __future__ import absolute_import

import logging

from fiona.errors import UnsupportedGeometryTypeError
from fiona._err cimport exc_wrap_int


class NullHandler(logging.Handler):
    def emit(self, record):
        pass

log = logging.getLogger(__name__)
log.addHandler(NullHandler())

# Mapping of OGR integer geometry types to GeoJSON type names.
GEOMETRY_TYPES = {
    0: 'Unknown',
    1: 'Point',
    2: 'LineString',
    3: 'Polygon',
    4: 'MultiPoint',
    5: 'MultiLineString',
    6: 'MultiPolygon',
    7: 'GeometryCollection',
    # Unsupported types.
    #8: 'CircularString',
    #9: 'CompoundCurve',
    #10: 'CurvePolygon',
    #11: 'MultiCurve',
    #12: 'MultiSurface',
    #13: 'Curve',
    #14: 'Surface',
    #15: 'PolyhedralSurface',
    #16: 'TIN',
    #17: 'Triangle',
    100: 'None',
    101: 'LinearRing',
    0x80000001: '3D Point',
    0x80000002: '3D LineString',
    0x80000003: '3D Polygon',
    0x80000004: '3D MultiPoint',
    0x80000005: '3D MultiLineString',
    0x80000006: '3D MultiPolygon',
    0x80000007: '3D GeometryCollection' }

# mapping of GeoJSON type names to OGR integer geometry types
GEOJSON2OGR_GEOMETRY_TYPES = dict((v, k) for k, v in GEOMETRY_TYPES.iteritems())


cdef unsigned int geometry_type_code(name) except? 9999:
    """Map OGC geometry type names to integer codes."""
    offset = 0
    if name.endswith('ZM'):
        offset = 3000
    elif name.endswith('M'):
        offset = 2000
    elif name.endswith('Z'):
        offset = 1000

    normalized_name = name.rstrip('ZM')
    if normalized_name not in GEOJSON2OGR_GEOMETRY_TYPES:
        raise UnsupportedGeometryTypeError(name)

    return offset + <unsigned int>GEOJSON2OGR_GEOMETRY_TYPES[normalized_name]


cdef object normalize_geometry_type_code(unsigned int code):
    """Normalize M geometry type codes."""
    # Normalize 'M' types to 2D types.
    if 2000 <= code < 3000:
        code = code % 1000
    elif code == 3000:
        code = 0
    # Normalize 'ZM' types to 3D types.
    elif 3000 < code < 4000:
        code = (code % 1000) | 0x80000000
    if code not in GEOMETRY_TYPES:
        raise UnsupportedGeometryTypeError(code)

    return code


cdef inline unsigned int base_geometry_type_code(unsigned int code):
    """ Returns base geometry code without Z, M and ZM types """
    # Remove 2.5D flag.
    code = code & (~0x80000000)

    # Normalize Z, M, and ZM types. Fiona 1.x does not support M
    # and doesn't treat OGC 'Z' variants as special types of their
    # own.
    return code % 1000


# Geometry related functions and classes follow.
cdef void * _createOgrGeomFromWKB(object wkb) except NULL:
    """Make an OGR geometry from a WKB string"""
    wkbtype = bytearray(wkb)[1]
    cdef unsigned char *buffer = wkb
    cdef void *cogr_geometry = OGR_G_CreateGeometry(<OGRwkbGeometryType>wkbtype)
    if cogr_geometry is not NULL:
        exc_wrap_int(OGR_G_ImportFromWkb(cogr_geometry, buffer, len(wkb)))
    return cogr_geometry


cdef _deleteOgrGeom(void *cogr_geometry):
    """Delete an OGR geometry"""
    if cogr_geometry is not NULL:
        OGR_G_DestroyGeometry(cogr_geometry)
    cogr_geometry = NULL


cdef class GeomBuilder:
    """Builds Fiona (GeoJSON) geometries from an OGR geometry handle.
    """
    cdef _buildCoords(self, void *geom):
        # Build a coordinate sequence
        cdef int i
        if geom == NULL:
            raise ValueError("Null geom")
        npoints = OGR_G_GetPointCount(geom)
        coords = []
        for i in range(npoints):
            values = [OGR_G_GetX(geom, i), OGR_G_GetY(geom, i)]
            if self.ndims > 2:
                values.append(OGR_G_GetZ(geom, i))
            coords.append(tuple(values))
        return coords
    
    cpdef _buildPoint(self):
        return {'type': 'Point', 'coordinates': self._buildCoords(self.geom)[0]}
    
    cpdef _buildLineString(self):
        return {'type': 'LineString', 'coordinates': self._buildCoords(self.geom)}
    
    cpdef _buildLinearRing(self):
        return {'type': 'LinearRing', 'coordinates': self._buildCoords(self.geom)}
    
    cdef _buildParts(self, void *geom):
        cdef int j
        cdef void *part
        if geom == NULL:
            raise ValueError("Null geom")
        parts = []
        for j in range(OGR_G_GetGeometryCount(geom)):
            part = OGR_G_GetGeometryRef(geom, j)
            parts.append(GeomBuilder().build(part))
        return parts
    
    cpdef _buildPolygon(self):
        coordinates = [p['coordinates'] for p in self._buildParts(self.geom)]
        return {'type': 'Polygon', 'coordinates': coordinates}
    
    cpdef _buildMultiPoint(self):
        coordinates = [p['coordinates'] for p in self._buildParts(self.geom)]
        return {'type': 'MultiPoint', 'coordinates': coordinates}
    
    cpdef _buildMultiLineString(self):
        coordinates = [p['coordinates'] for p in self._buildParts(self.geom)]
        return {'type': 'MultiLineString', 'coordinates': coordinates}
    
    cpdef _buildMultiPolygon(self):
        coordinates = [p['coordinates'] for p in self._buildParts(self.geom)]
        return {'type': 'MultiPolygon', 'coordinates': coordinates}

    cpdef _buildGeometryCollection(self):
        parts = self._buildParts(self.geom)
        return {'type': 'GeometryCollection', 'geometries': parts}
    
    cdef build(self, void *geom):
        # The only method anyone needs to call
        if geom == NULL:
            raise ValueError("Null geom")

        cdef unsigned int etype = OGR_G_GetGeometryType(geom)

        self.code = base_geometry_type_code(etype)

        if self.code not in GEOMETRY_TYPES:
            raise UnsupportedGeometryTypeError(self.code)

        self.geomtypename = GEOMETRY_TYPES[self.code]
        self.ndims = OGR_G_GetCoordinateDimension(geom)
        self.geom = geom
        return getattr(self, '_build' + self.geomtypename)()

    cpdef build_wkb(self, object wkb):
        # The only other method anyone needs to call
        cdef object data = wkb
        cdef void *cogr_geometry = _createOgrGeomFromWKB(data)
        result = self.build(cogr_geometry)
        _deleteOgrGeom(cogr_geometry)
        return result


cdef class OGRGeomBuilder:
    """Builds OGR geometries from Fiona geometries.
    """
    cdef void * _createOgrGeometry(self, int geom_type) except NULL:
        cdef void *cogr_geometry = OGR_G_CreateGeometry(<OGRwkbGeometryType>geom_type)
        if cogr_geometry == NULL:
            raise Exception("Could not create OGR Geometry of type: %i" % geom_type)
        return cogr_geometry

    cdef _addPointToGeometry(self, void *cogr_geometry, object coordinate):
        if len(coordinate) == 2:
            x, y = coordinate
            OGR_G_AddPoint_2D(cogr_geometry, x, y)
        else:
            x, y, z = coordinate[:3]
            OGR_G_AddPoint(cogr_geometry, x, y, z)

    cdef void * _buildPoint(self, object coordinates) except NULL:
        cdef void *cogr_geometry = self._createOgrGeometry(GEOJSON2OGR_GEOMETRY_TYPES['Point'])
        self._addPointToGeometry(cogr_geometry, coordinates)
        return cogr_geometry
    
    cdef void * _buildLineString(self, object coordinates) except NULL:
        cdef void *cogr_geometry = self._createOgrGeometry(GEOJSON2OGR_GEOMETRY_TYPES['LineString'])
        for coordinate in coordinates:
            self._addPointToGeometry(cogr_geometry, coordinate)
        return cogr_geometry
    
    cdef void * _buildLinearRing(self, object coordinates) except NULL:
        cdef void *cogr_geometry = self._createOgrGeometry(GEOJSON2OGR_GEOMETRY_TYPES['LinearRing'])
        for coordinate in coordinates:
            self._addPointToGeometry(cogr_geometry, coordinate)
        OGR_G_CloseRings(cogr_geometry)
        return cogr_geometry
    
    cdef void * _buildPolygon(self, object coordinates) except NULL:
        cdef void *cogr_ring
        cdef void *cogr_geometry = self._createOgrGeometry(GEOJSON2OGR_GEOMETRY_TYPES['Polygon'])
        for ring in coordinates:
            cogr_ring = self._buildLinearRing(ring)
            exc_wrap_int(OGR_G_AddGeometryDirectly(cogr_geometry, cogr_ring))
        return cogr_geometry

    cdef void * _buildMultiPoint(self, object coordinates) except NULL:
        cdef void *cogr_part
        cdef void *cogr_geometry = self._createOgrGeometry(GEOJSON2OGR_GEOMETRY_TYPES['MultiPoint'])
        for coordinate in coordinates:
            cogr_part = self._buildPoint(coordinate)
            exc_wrap_int(OGR_G_AddGeometryDirectly(cogr_geometry, cogr_part))
        return cogr_geometry

    cdef void * _buildMultiLineString(self, object coordinates) except NULL:
        cdef void *cogr_part
        cdef void *cogr_geometry = self._createOgrGeometry(GEOJSON2OGR_GEOMETRY_TYPES['MultiLineString'])
        for line in coordinates:
            cogr_part = self._buildLineString(line)
            exc_wrap_int(OGR_G_AddGeometryDirectly(cogr_geometry, cogr_part))
        return cogr_geometry

    cdef void * _buildMultiPolygon(self, object coordinates) except NULL:
        cdef void *cogr_part
        cdef void *cogr_geometry = self._createOgrGeometry(GEOJSON2OGR_GEOMETRY_TYPES['MultiPolygon'])
        for part in coordinates:
            cogr_part = self._buildPolygon(part)
            exc_wrap_int(OGR_G_AddGeometryDirectly(cogr_geometry, cogr_part))
        return cogr_geometry

    cdef void * _buildGeometryCollection(self, object coordinates) except NULL:
        cdef void *cogr_part
        cdef void *cogr_geometry = self._createOgrGeometry(GEOJSON2OGR_GEOMETRY_TYPES['GeometryCollection'])
        for part in coordinates:
            cogr_part = OGRGeomBuilder().build(part)
            exc_wrap_int(OGR_G_AddGeometryDirectly(cogr_geometry, cogr_part))
        return cogr_geometry

    cdef void * build(self, object geometry) except NULL:
        cdef object typename = geometry['type']
        cdef object coordinates = geometry.get('coordinates')
        if typename == 'Point':
            return self._buildPoint(coordinates)
        elif typename == 'LineString':
            return self._buildLineString(coordinates)
        elif typename == 'LinearRing':
            return self._buildLinearRing(coordinates)
        elif typename == 'Polygon':
            return self._buildPolygon(coordinates)
        elif typename == 'MultiPoint':
            return self._buildMultiPoint(coordinates)
        elif typename == 'MultiLineString':
            return self._buildMultiLineString(coordinates)
        elif typename == 'MultiPolygon':
            return self._buildMultiPolygon(coordinates)
        elif typename == 'GeometryCollection':
            coordinates = geometry.get('geometries')
            return self._buildGeometryCollection(coordinates)
        else:
            raise ValueError("Unsupported geometry type %s" % typename)


def geometryRT(geometry):
    # For testing purposes only, leaks the JSON data
    cdef void *cogr_geometry = OGRGeomBuilder().build(geometry)
    result = GeomBuilder().build(cogr_geometry)
    _deleteOgrGeom(cogr_geometry)
    return result
