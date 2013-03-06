# Making maps with reduce()

from matplotlib import pyplot
from descartes import PolygonPatch
import fiona

BLUE = '#6699cc'

def render(fig, rec):
    """Given matplotlib axes and a record, adds the record as a patch
    and returns the axes so that reduce() can accumulate more
    patches."""
    fig.gca().add_patch(
        PolygonPatch(rec['geometry'], fc=BLUE, ec=BLUE, alpha=0.5, zorder=2))
    return fig

with fiona.open('docs/data/test_uk.shp', 'r') as source:
    fig = reduce(render, source, pyplot.figure(figsize=(8, 8)))
    fig.gca().autoscale(tight=False)
    fig.savefig('with-descartes-functional.png')

