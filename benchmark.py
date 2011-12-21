
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
layer.ResetReading()
while 1:
    feature = layer.GetNextFeature()
    if not feature:
        break
    id = feature.GetFID()
    props = {}
    for i in range(feature.GetFieldCount()):
        props[schema[i][0]] = feature.GetField(i)
    geometry = feature.GetGeometryRef()
    feature.Destroy()
source.Destroy()
"""
print "osgeo.ogr 1.7.2"
t = timeit.Timer(
    stmt=s,
    setup='from __main__ import ogr, PATH, NAME'
    )
print "%.2f usec/pass" % (1000000 * t.timeit(number=1000)/1000)

