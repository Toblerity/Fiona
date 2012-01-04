
import timeit
from fiona import collection
from osgeo import ogr

PATH = 'docs/data/test_uk.shp'
NAME = 'test_uk'

# Fiona
s = """
with collection(PATH, "r") as c:
    for f in c:
        id = f["id"]
"""
t = timeit.Timer(
    stmt=s,
    setup='from __main__ import collection, PATH, NAME'
    )
print "Fiona 0.5"
print "%.2f usec/pass" % (1000000 * t.timeit(number=1000)/1000)
print

# OGR
s = """
source = ogr.Open(PATH)
layer = source.GetLayerByName(NAME)

schema = []
ldefn = layer.GetLayerDefn()
for n in range(ldefn.GetFieldCount()):
    fdefn = ldefn.GetFieldDefn(n)
    schema.append((fdefn.name, fdefn.type))

for feature in layer:
    id = feature.GetFID()
    props = {}
    for i in range(feature.GetFieldCount()):
        props[schema[i][0]] = feature.GetField(i)
    
    coordinates = []
    for part in feature.GetGeometryRef():
        ring = []
        for i in range(part.GetPointCount()):
            xy = part.GetPoint(i)
            ring.append(xy)
        coordinates.append(ring)

source.Destroy()
"""
print "osgeo.ogr 1.7.2 (maximum)"
t = timeit.Timer(
    stmt=s,
    setup='from __main__ import ogr, PATH, NAME'
    )
print "%.2f usec/pass" % (1000000 * t.timeit(number=1000)/1000)

