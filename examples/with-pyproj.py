
import logging
import sys

from pyproj import Proj, transform

import fiona
from fiona.crs import from_epsg

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

with fiona.open('docs/data/test_uk.shp', 'r') as source:
    
    sink_schema = source.schema.copy()
    p_in = Proj(source.crs)

    with fiona.open(
            'with-pyproj.shp', 'w',
            crs=from_epsg(27700),
            driver=source.driver,
            schema=sink_schema,
            ) as sink:
        
        p_out = Proj(sink.crs)

        for f in source:
            
            try:
                assert f['geometry']['type'] == "Polygon"
                new_coords = []
                for ring in f['geometry']['coordinates']:
                    x2, y2 = transform(p_in, p_out, *zip(*ring))
                    new_coords.append(zip(x2, y2))
                f['geometry']['coordinates'] = new_coords
                sink.write(f)
            
            except Exception, e:
                # Writing uncleanable features to a different shapefile
                # is another option.
                logging.exception("Error transforming feature %s:", f['id'])

