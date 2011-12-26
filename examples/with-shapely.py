
import logging
import sys

from shapely.geometry import mapping, shape

from fiona import collection


logging.basicConfig(stream=sys.stderr, level=logging.INFO)

with collection("docs/data/test_uk.shp", "r") as input:
    
    schema = input.schema.copy()
    
    with collection(
            "with-shapely.shp", "w", "ESRI Shapefile", schema
            ) as output:
        
        for f in input:
            
            try:
                geom = shape(f['geometry'])
                if not geom.is_valid:
                    clean = geom.buffer(0.0)
                    assert clean.is_valid
                    assert clean.geom_type == 'Polygon'
                    geom = clean
                f['geometry'] = mapping(geom)
                output.write(f)
            
            except Exception, e:
                # Writing uncleanable features to a different shapefile
                # is another option.
                logging.exception("Error cleaning feature %s:", f['id'])

