import glob
import os
from collections import defaultdict
import re

ignored_files = {'_shim.pyx', '_shim1.pyx', '_shim1.pxd', 'ogrext1.pxd'}

# List of deprecated methods from https://gdal.org/doxygen/deprecated.html#_deprecated000028
deprecated = {
    'CPL_LSBINT16PTR',
    'CPL_LSBINT32PTR(x)',
    'OGR_Dr_CopyDataSource',
    'OGR_Dr_CreateDataSource',
    'OGR_Dr_DeleteDataSource',
    'OGR_Dr_Open',
    'OGR_Dr_TestCapability',
    'OGR_DS_CopyLayer',
    'OGR_DS_CreateLayer',
    'OGR_DS_DeleteLayer',
    'OGR_DS_Destroy',
    'OGR_DS_ExecuteSQL',
    'OGR_DS_GetDriver',
    'OGR_DS_GetLayer',
    'OGR_DS_GetLayerByName',
    'OGR_DS_GetLayerCount',
    'OGR_DS_GetName',
    'OGR_DS_ReleaseResultSet',
    'OGR_DS_TestCapability',
    'OGR_G_GetCoordinateDimension',
    'OGR_G_SetCoordinateDimension',
    'OGRGetDriver',
    'OGRGetDriverByName',
    'OGRGetDriverCount',
    'OGROpen',
    'OGROpenShared',
    'OGRRegisterAll',
    'OGRReleaseDataSource',
}

found_lines = defaultdict(list)
files = glob.glob('fiona/*.pyx') + glob.glob('fiona/*.pxd')
for path in files:
    if os.path.basename(path) in ignored_files:
        continue

    with open(path, 'r') as f:
        for i, line in enumerate(f):
            for deprecated_method in deprecated:
                match = re.search('{}\s*\('.format(deprecated_method), line)
                if match:
                    found_lines[path].append((i+1, line.strip(), deprecated_method))

for path in sorted(found_lines):
    print(path)
    for line_nr, line, method in found_lines[path]:
        print("\t{}\t{}".format(line_nr, line))
    print("")
