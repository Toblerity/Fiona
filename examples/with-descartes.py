
import logging
import sys

from matplotlib import pyplot
from descartes import PolygonPatch

from fiona import collection


BLUE = '#6699cc'
fig = pyplot.figure(1, figsize=(6, 6), dpi=90)
ax = fig.add_subplot(111)

input = collection("docs/data/test_uk.shp", "r")
for f in input:
    patch = PolygonPatch(f['geometry'], fc=BLUE, ec=BLUE, alpha=0.5, zorder=2)
    ax.add_patch(patch)

# Should be able to get extents from the collection in a future version
# of Fiona.
ax.set_xlim(-9.25, 2.75)
ax.set_ylim(49.5, 61.5)
fig.savefig('test_uk.png')

