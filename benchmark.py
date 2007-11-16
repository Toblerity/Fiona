
import timeit
import mill
import ogr

PATH = 'docs/data'
NAME = 'test_uk'

# WorldMill
s = """
w = mill.workspace(PATH)
c = w[NAME]
for f in c:
    id = f.id
"""
t = timeit.Timer(
    stmt=s,
    setup='from __main__ import mill, PATH, NAME'
    )
print "WorldMill (Cython)"
print "%.2f usec/pass" % (1000000 * t.timeit(number=100)/100)
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
print "ogr.py (new bindings)"
t = timeit.Timer(
    stmt=s,
    setup='from __main__ import ogr, PATH, NAME'
    )
print "%.2f usec/pass" % (1000000 * t.timeit(number=100)/100)

