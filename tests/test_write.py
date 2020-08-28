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
