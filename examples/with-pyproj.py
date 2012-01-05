
import logging
import sys

from pyproj import Proj, transform

from fiona import collection


logging.basicConfig(stream=sys.stderr, level=logging.INFO)

with collection("docs/data/test_uk.shp", "r") as input:
    
    schema = input.schema.copy()
    p_in = Proj(input.crs)

    with collection(
            "with-pyproj.shp", "w", "ESRI Shapefile",
            schema=schema,
            crs={'init': "epsg:27700", 'no_defs': True}
            ) as output:
        
        p_out = Proj(output.crs)
        for f in input:
            
            try:
                assert f['geometry']['type'] == "Polygon"
                new_coords = []
                for ring in f['geometry']['coordinates']:
                    x2, y2 = transform(p_in, p_out, *zip(*ring))
                    new_coords.append(zip(x2, y2))
                f['geometry']['coordinates'] = new_coords
                output.write(f)
            
            except Exception, e:
                # Writing uncleanable features to a different shapefile
                # is another option.
                logging.exception("Error transforming feature %s:", f['id'])

