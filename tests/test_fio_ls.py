"""Unittests for `$ fio ls`"""


import json
import sys
import os
from click.testing import CliRunner
import pytest
import fiona
from fiona.fio.main import main_group

DATA_DIR = os.path.join("tests", "data")

def test_fio_ls_single_layer():

    result = CliRunner().invoke(main_group, [
        'ls',
        DATA_DIR])
    assert result.exit_code == 0
    assert len(result.output.splitlines()) == 1
    assert json.loads(result.output) == ['coutwildrnp']


def test_fio_ls_indent(path_coutwildrnp_shp):

    result = CliRunner().invoke(main_group, [
        'ls',
        '--indent', '4',
        path_coutwildrnp_shp])
    assert result.exit_code == 0
    assert len(result.output.strip().splitlines()) == 3
    assert json.loads(result.output) == ['coutwildrnp']


def test_fio_ls_multi_layer(path_coutwildrnp_shp, tmpdir):
    outdir = str(tmpdir.mkdir('test_fio_ls_multi_layer'))

    # Copy test shapefile into new directory
    # Shapefile driver treats a directory of shapefiles as a single
    # multi-layer datasource
    layer_names = ['l1', 'l2']
    for layer in layer_names:
        with fiona.open(path_coutwildrnp_shp) as src, \
                fiona.open(outdir, 'w', layer=layer, **src.meta) as dst:
            for feat in src:
                dst.write(feat)

    # Run CLI test
    result = CliRunner().invoke(main_group, [
        'ls', outdir])
    assert result.exit_code == 0
    assert json.loads(result.output) == layer_names


def test_fio_ls_vfs(path_coutwildrnp_zip):
    runner = CliRunner()
    result = runner.invoke(main_group, [
        'ls', 'zip://{}'.format(path_coutwildrnp_zip)])
    assert result.exit_code == 0
    loaded = json.loads(result.output)
    assert len(loaded) == 1
    assert loaded[0] == 'coutwildrnp'
