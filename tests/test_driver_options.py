import os
import tempfile
from collections import OrderedDict
import glob
import fiona
from tests.conftest import get_temp_filename, requires_gdal2


@requires_gdal2
def test_gml_format_option():
    """ Test GML dataset creation option FORMAT (see https://github.com/Toblerity/Fiona/issues/968)"""

    schema = {'geometry': 'Point', 'properties': OrderedDict([('position', 'int')])}
    records = [{'geometry': {'type': 'Point', 'coordinates': (0.0, float(i))}, 'properties': {'position': i}} for i in
               range(10)]

    tmpdir = tempfile.mkdtemp()
    fpath = os.path.join(tmpdir, get_temp_filename('GML'))

    with fiona.open(fpath,
                    'w',
                    driver="GML",
                    schema=schema,
                    FORMAT="GML3") as out:
        out.writerecords(records)

    xsd_path = glob.glob(os.path.join(tmpdir, "*.xsd"))[0]
    with open(xsd_path) as f:
        xsd = f.read()
        assert "http://schemas.opengis.net/gml/3.1.1" in xsd
