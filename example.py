import fiona
from fiona.model import Feature, Geometry, Properties
from shapely.geometry import mapping, shape

# Open a file for reading. We'll call this the source.
with fiona.open("tests/data/coutwildrnp.shp") as src:

    # The file we'll write to must be initialized with a coordinate
    # system, a format driver name, and a record schema. We can get
    # initial values from the open source's meta property and then
    # modify them as we need.
    meta = src.meta
    meta["schema"]["geometry"] = "Point"
    meta["driver"] = "GPKG"

    # Open an output file, using the same format driver and coordinate
    # reference system as the source. The meta mapping fills in the
    # keyword parameters of fiona.open.
    with fiona.open("/tmp/example.gpkg", "w", **meta) as dst:

        # Process only the records intersecting a box.
        for f in src.filter(bbox=(-107.0, 37.0, -105.0, 39.0)):

            # Get the feature's centroid.
            centroid = shape(dict(**f.geometry)).centroid
            new_geom = Geometry.from_dict(**mapping(centroid))

            # Write the feature out.
            dst.write(
                Feature(
                    geometry=new_geom, properties=Properties.from_dict(**f.properties)
                )
            )
