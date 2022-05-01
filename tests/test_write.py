"""New tests of writing feature collections."""

import fiona
from fiona.crs import from_epsg


def test_issue771(tmpdir, caplog):
    """Overwrite a GeoJSON file without logging errors."""
    schema = {"geometry": "Point", "properties": {"zero": "int"}}

    feature = {
        "geometry": {"type": "Point", "coordinates": (0, 0)},
        "properties": {"zero": "0"},
    }

    outputfile = tmpdir.join("test.geojson")

    for i in range(2):
        with fiona.open(
            str(outputfile), "w", driver="GeoJSON", schema=schema, crs=from_epsg(4326)
        ) as collection:
            collection.write(feature)
        assert outputfile.exists()

    for record in caplog.records:
        assert record.levelname != "ERROR"


def test_write__esri_only_wkt(tmpdir):
    """https://github.com/Toblerity/Fiona/issues/977"""
    schema = {"geometry": "Point", "properties": {"zero": "int"}}
    feature = {
        "geometry": {"type": "Point", "coordinates": (0, 0)},
        "properties": {"zero": "0"},
    }
    target_crs = (
        'PROJCS["IaRCS_04_Sioux_City-Iowa_Falls_NAD_1983_2011_LCC_US_Feet",'
        'GEOGCS["GCS_NAD_1983_2011",DATUM["D_NAD_1983_2011",'
        'SPHEROID["GRS_1980",6378137.0,298.257222101]],'
        'PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],'
        'PROJECTION["Lambert_Conformal_Conic"],'
        'PARAMETER["False_Easting",14500000.0],'
        'PARAMETER["False_Northing",8600000.0],'
        'PARAMETER["Central_Meridian",-94.83333333333333],'
        'PARAMETER["Standard_Parallel_1",42.53333333333333],'
        'PARAMETER["Standard_Parallel_2",42.53333333333333],'
        'PARAMETER["Scale_Factor",1.000045],'
        'PARAMETER["Latitude_Of_Origin",42.53333333333333],'
        'UNIT["Foot_US",0.3048006096012192]]'
    )
    outputfile = tmpdir.join("test.shp")
    with fiona.open(
        str(outputfile), "w",
        driver="ESRI Shapefile",
        schema=schema,
        crs=target_crs,
    ) as collection:
        collection.write(feature)
        assert collection.crs_wkt.startswith(
            (
                'PROJCS["IaRCS_04_Sioux_City-Iowa_Falls_NAD_1983_2011_LCC_US_Feet"',
                'PROJCRS["IaRCS_04_Sioux_City-Iowa_Falls_NAD_1983_2011_LCC_US_Feet"'  # GDAL 3.3+
            )
        )


def test_write__wkt_version(tmpdir):
    """https://github.com/Toblerity/Fiona/issues/977"""
    schema = {"geometry": "Point", "properties": {"zero": "int"}}
    feature = {
        "geometry": {"type": "Point", "coordinates": (0, 0)},
        "properties": {"zero": "0"},
    }
    target_crs = (
        'PROJCS["IaRCS_04_Sioux_City-Iowa_Falls_NAD_1983_2011_LCC_US_Feet",'
        'GEOGCS["GCS_NAD_1983_2011",DATUM["D_NAD_1983_2011",'
        'SPHEROID["GRS_1980",6378137.0,298.257222101]],'
        'PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],'
        'PROJECTION["Lambert_Conformal_Conic"],'
        'PARAMETER["False_Easting",14500000.0],'
        'PARAMETER["False_Northing",8600000.0],'
        'PARAMETER["Central_Meridian",-94.83333333333333],'
        'PARAMETER["Standard_Parallel_1",42.53333333333333],'
        'PARAMETER["Standard_Parallel_2",42.53333333333333],'
        'PARAMETER["Scale_Factor",1.000045],'
        'PARAMETER["Latitude_Of_Origin",42.53333333333333],'
        'UNIT["Foot_US",0.3048006096012192]]'
    )
    outputfile = tmpdir.join("test.shp")
    with fiona.open(
        str(outputfile), "w",
        driver="ESRI Shapefile",
        schema=schema,
        crs=target_crs,
        wkt_version="WKT2_2018",
    ) as collection:
        collection.write(feature)
        assert collection.crs_wkt.startswith(
            'PROJCRS["IaRCS_04_Sioux_City-Iowa_Falls_NAD_1983_2011_LCC_US_Feet"'
        )
