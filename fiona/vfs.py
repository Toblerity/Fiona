"""Implementation of Apache VFS schemes and URLs."""

import os

# NB: As not to propagate fallacies of distributed computing, Rasterio
# does not support HTTP or FTP URLs via GDAL's vsicurl handler. Only
# the following local filesystem schemes are supported.
SCHEMES = {'gzip': 'gzip', 'zip': 'zip', 'tar': 'tar', 'https': 'curl',
           'http': 'curl', 's3': 's3'}

def valid_vsi(vsi):
    """Ensure all parts of our vsi path are valid schemes."""
    return all(p in SCHEMES for p in vsi.split('+'))

def vsi_path(path, vsi=None, archive=None):
    # If a VSF and archive file are specified, we convert the path to
    # an OGR VSI path (see cpl_vsi.h).
    if vsi:
        prefix = '/'.join('vsi{0}'.format(SCHEMES[p]) for p in vsi.split('+'))
        if archive:
            result = '/{0}/{1}{2}'.format(prefix, archive, path)
        else:
            result = '/{0}/{1}'.format(prefix, path)
    else:
        result = path

    return result

