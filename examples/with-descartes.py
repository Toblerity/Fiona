
from matplotlib import pyplot
from descartes import PolygonPatch

from fiona import collection

# Set up the figure and axes.
BLUE = '#6699cc'
fig = pyplot.figure(1, figsize=(6, 6), dpi=90)
ax = fig.add_subplot(111)

# For each feature in the collection, add a patch to the axes.
with collection("docs/data/test_uk.shp", "r") as input:
    for f in input:
        ax.add_patch(
            PolygonPatch(
                f['geometry'], fc=BLUE, ec=BLUE, alpha=0.5, zorder=2 ))

# Should be able to get extents from the collection in a future version
# of Fiona.
ax.set_xlim(-9.25, 2.75)
ax.set_ylim(49.5, 61.5)

fig.savefig('test_uk.png')

