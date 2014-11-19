import os

DATADIR = os.path.abspath('tests/data')
FILES = ['coutwildrnp.shp', 'coutwildrnp.shx', 'coutwildrnp.dbf', 'coutwildrnp.prj']

def create_zipfile(zipfilename):
    import zipfile
    with zipfile.ZipFile(zipfilename, 'w') as zip:
        for filename in FILES:
            zip.write(os.path.join(DATADIR, filename), filename)

def create_tarfile(tarfilename):
    import tarfile
    with tarfile.open(tarfilename, 'w') as tar:
        for filename in FILES:
            tar.add(os.path.join(DATADIR, filename), arcname='testing/%s' % filename)

def create_jsonfile(jsonfilename):
    import json
    import fiona
    with fiona.open(os.path.join(DATADIR, FILES[0]), 'r') as source:
        features = [feat for feat in source]
    my_layer = {'type': 'FeatureCollection',
                'features': features}
    with open(jsonfilename, 'w') as f:
        f.write(json.dumps(my_layer))

def setup():
    """Setup function for nosetests to create test files if they do not exist
    """
    zipfile = os.path.join(DATADIR, 'coutwildrnp.zip')
    tarfile = os.path.join(DATADIR, 'coutwildrnp.tar')
    jsonfile = os.path.join(DATADIR, 'coutwildrnp.json')
    if not os.path.exists(zipfile):
        create_zipfile(zipfile)
    if not os.path.exists(tarfile):
        create_tarfile(tarfile)
    if not os.path.exists(jsonfile):
        create_jsonfile(jsonfile)
