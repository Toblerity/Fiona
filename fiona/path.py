"""Dataset paths, identifiers, and filenames"""

import re
import sys

import attr

from fiona.compat import urlparse

# Supported URI schemes and their mapping to GDAL's VSI suffix.
# TODO: extend for other cloud plaforms.
SCHEMES = {
    'ftp': 'curl',
    'gzip': 'gzip',
    'http': 'curl',
    'https': 'curl',
    's3': 's3',
    'tar': 'tar',
    'zip': 'zip',
    'file': 'file'
}

CURLSCHEMES = set([k for k, v in SCHEMES.items() if v == 'curl'])

# TODO: extend for other cloud plaforms.
REMOTESCHEMES = set([k for k, v in SCHEMES.items() if v in ('curl', 's3')])


class Path(object):
    """Base class for dataset paths"""


@attr.s(slots=True)
class ParsedPath(Path):
    """Result of parsing a dataset URI/Path

    Attributes
    ----------
    path : str
        Parsed path. Includes the hostname and query string in the case
        of a URI.
    archive : str
        Parsed archive path.
    scheme : str
        URI scheme such as "https" or "zip+s3".
    """
    path = attr.ib()
    archive = attr.ib()
    scheme = attr.ib()

    @classmethod
    def from_uri(cls, uri):
        parts = urlparse(uri)
        path = parts.path
        scheme = parts.scheme or None

        if parts.query:
            path += "?" + parts.query

        if parts.scheme and parts.netloc:
            path = parts.netloc + path

        parts = path.split('!')
        path = parts.pop() if parts else None
        archive = parts.pop() if parts else None
        return ParsedPath(path, archive, scheme)

    @property
    def name(self):
        """The parsed path's original URI"""
        if not self.scheme:
            return self.path
        elif self.archive:
            return "{}://{}!{}".format(self.scheme, self.archive, self.path)
        else:
            return "{}://{}".format(self.scheme, self.path)

    @property
    def is_remote(self):
        """Test if the path is a remote, network URI"""
        return self.scheme and self.scheme.split('+')[-1] in REMOTESCHEMES

    @property
    def is_local(self):
        """Test if the path is a local URI"""
        return not self.scheme or (self.scheme and self.scheme.split('+')[-1] not in REMOTESCHEMES)


@attr.s(slots=True)
class UnparsedPath(Path):
    """Encapsulates legacy GDAL filenames

    Attributes
    ----------
    path : str
        The legacy GDAL filename.
    """
    path = attr.ib()

    @property
    def name(self):
        """The unparsed path's original path"""
        return self.path


def parse_path(path):
    """Parse a dataset's identifier or path into its parts

    Parameters
    ----------
    path : str or path-like object
        The path to be parsed.

    Returns
    -------
    ParsedPath or UnparsedPath

    Notes
    -----
    When legacy GDAL filenames are encountered, they will be returned
    in a UnparsedPath.
    """
    if isinstance(path, Path):
        return path

    # Windows drive letters (e.g. "C:\") confuse `urlparse` as they look like
    # URL schemes
    elif sys.platform == "win32" and re.match("^[a-zA-Z]\\:", path):
        return UnparsedPath(path)

    elif path.startswith('/vsi'):
        return UnparsedPath(path)

    else:
        parts = urlparse(path)

        # if the scheme is not one of Rasterio's supported schemes, we
        # return an UnparsedPath.
        if parts.scheme and not all(p in SCHEMES for p in parts.scheme.split('+')):
            return UnparsedPath(path)

        else:
            return ParsedPath.from_uri(path)


def vsi_path(path):
    """Convert a parsed path to a GDAL VSI path

    Parameters
    ----------
    path : Path
        A ParsedPath or UnparsedPath object.

    Returns
    -------
    str
    """
    if isinstance(path, UnparsedPath):
        return path.path

    elif isinstance(path, ParsedPath):

        if not path.scheme:
            return path.path

        else:
            if path.scheme.split('+')[-1] in CURLSCHEMES:
                suffix = '{}://'.format(path.scheme.split('+')[-1])
            else:
                suffix = ''

            prefix = '/'.join('vsi{0}'.format(SCHEMES[p]) for p in path.scheme.split('+') if p != 'file')

            if prefix:
                if path.archive:
                    result = '/{}/{}{}/{}'.format(prefix, suffix, path.archive, path.path.lstrip('/'))
                else:
                    result = '/{}/{}{}'.format(prefix, suffix, path.path)
            else:
                result = path.path
            return result

    else:
        raise ValueError("path must be a ParsedPath or UnparsedPath object")
