"""Unittests for `$ fio ls`"""


import json
import shutil
import sys
import tempfile
import unittest

from click.testing import CliRunner

import fiona
from fiona.fio.main import main_group

FIXME_WINDOWS = sys.platform.startswith('win')

@unittest.skipIf(FIXME_WINDOWS, 
                 reason="FIXME on Windows. Please look into why this test is not working.")
def test_fio_ls_single_layer():

    result = CliRunner().invoke(main_group, [
        'ls',
        'tests/data/'])
    assert result.exit_code == 0
    assert len(result.output.splitlines()) == 1
    assert json.loads(result.output) == ['coutwildrnp']


@unittest.skipIf(FIXME_WINDOWS, 
                 reason="FIXME on Windows. Please look into why this test is not working.")
def test_fio_ls_indent():

    result = CliRunner().invoke(main_group, [
        'ls',
        '--indent', '4',
        'tests/data/coutwildrnp.shp'])
    assert result.exit_code == 0
    assert len(result.output.strip().splitlines()) == 3
    assert json.loads(result.output) == ['coutwildrnp']


def test_fio_ls_multi_layer():

    infile = 'tests/data/coutwildrnp.shp'
    outdir = tempfile.mkdtemp()
    try:
        
        # Copy test shapefile into new directory
        # Shapefile driver treats a directory of shapefiles as a single
        # multi-layer datasource
        layer_names = ['l1', 'l2']
        for layer in layer_names:
            with fiona.open(infile) as src, \
                    fiona.open(outdir, 'w', layer=layer, **src.meta) as dst:
                for feat in src:
                    dst.write(feat)

        # Run CLI test
        result = CliRunner().invoke(main_group, [
            'ls', outdir])
        assert result.exit_code == 0
        assert json.loads(result.output) == layer_names

    finally:
        shutil.rmtree(outdir)
