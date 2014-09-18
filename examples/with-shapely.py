
import logging
import sys

from shapely.geometry import mapping, shape

import fiona

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

with fiona.open('docs/data/test_uk.shp', 'r') as source:
    
    # **source.meta is a shortcut to get the crs, driver, and schema
    # keyword arguments from the source Collection.
    with fiona.open(
            'with-shapely.shp', 'w',
            **source.meta) as sink:
        
        for f in source:
            
            try:
                geom = shape(f['geometry'])
                if not geom.is_valid:
                    clean = geom.buffer(0.0)
                    assert clean.is_valid
                    assert clean.geom_type == 'Polygon'
                    geom = clean
                f['geometry'] = mapping(geom)
                sink.write(f)
            
            except Exception, e:
                # Writing uncleanable features to a different shapefile
                # is another option.
                logging.exception("Error cleaning feature %s:", f['id'])

