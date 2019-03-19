"""Tests of driver support"""

import pytest

import fiona.drvsupport


@pytest.mark.parametrize('format', ['GeoJSON', 'ESRIJSON', 'TopoJSON', 'GeoJSONSeq'])
def test_geojsonseq(format):
    """Format is available"""
    assert format in fiona.drvsupport.supported_drivers.keys()
