
import timeit
import mill
import ogr

PATH = '/var/gis/data/world'
NAME = 'world_borders'

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
print "%.2f usec/pass" % (1000000 * t.timeit(number=10)/10)
print

# OGR
s = """
source = ogr.Open(PATH)
layer = source.GetLayerByName(NAME)
layer.ResetReading()
while 1:
    feature = layer.GetNextFeature()
    if not feature:
        break
    id = feature.GetFID()
    feature.Destroy()
source.Destroy()
"""
print "ogr.py (new bindings)"
t = timeit.Timer(
    stmt=s,
    setup='from __main__ import ogr, PATH, NAME'
    )
print "%.2f usec/pass" % (1000000 * t.timeit(number=10)/10)

