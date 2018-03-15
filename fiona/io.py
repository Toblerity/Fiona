"""Classes capable of reading and writing collections
"""

from collections import OrderedDict
import logging

from fiona.ogrext import MemoryFileBase
from fiona.collection import Collection


log = logging.getLogger(__name__)


class MemoryFile(MemoryFileBase):
    """A BytesIO-like object, backed by an in-memory file.

    This allows formatted files to be read and written without I/O.

    A MemoryFile created with initial bytes becomes immutable. A
    MemoryFile created without initial bytes may be written to using
    either file-like or dataset interfaces.

    Examples
    --------

    """
    def __init__(self, file_or_bytes=None, filename=None, ext=''):
        super(MemoryFile, self).__init__(
            file_or_bytes=file_or_bytes, filename=filename, ext=ext)

    def open(self, driver=None, schema=None, crs=None, encoding=None,
             layer=None, vfs=None, enabled_drivers=None, crs_wkt=None,
             **kwargs):
        """Open the file and return a Fiona collection object.

        If data has already been written, the file is opened in 'r'
        mode. Otherwise, the file is opened in 'w' mode.

        Parameters
        ----------
        Note well that there is no `path` parameter: a `MemoryFile`
        contains a single dataset and there is no need to specify a
        path.

        Other parameters are optional and have the same semantics as the
        parameters of `fiona.open()`.
        """
        vsi_path = self.name

        if self.closed:
            raise IOError("I/O operation on closed file.")
        if self.exists():
            return Collection(vsi_path, 'r', driver=driver, encoding=encoding,
                              layer=layer, enabled_drivers=enabled_drivers,
                              **kwargs)
        else:
            if schema:
                # Make an ordered dict of schema properties.
                this_schema = schema.copy()
                this_schema['properties'] = OrderedDict(schema['properties'])
            else:
                this_schema = None
            return Collection(vsi_path, 'w', crs=crs, driver=driver,
                              schema=this_schema, encoding=encoding,
                              layer=layer, enabled_drivers=enabled_drivers,
                              crs_wkt=crs_wkt, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.close()


class ZipMemoryFile(MemoryFile):
    """A read-only BytesIO-like object backed by an in-memory zip file.

    This allows a zip file containing formatted files to be read
    without I/O.
    """

    def __init__(self, file_or_bytes=None):
        super(ZipMemoryFile, self).__init__(file_or_bytes, ext='zip')

    def open(self, path, driver=None, encoding=None, layer=None,
             enabled_drivers=None, **kwargs):
        """Open a dataset within the zipped stream.

        Parameters
        ----------
        path : str
            Path to a dataset in the zip file, relative to the root of the
            archive.

        Returns
        -------
        A Fiona collection object
        """
        vsi_path = '/vsizip{0}/{1}'.format(self.name, path.lstrip('/'))

        if self.closed:
            raise IOError("I/O operation on closed file.")
        return Collection(vsi_path, 'r', driver=driver, encoding=encoding,
                          layer=layer, enabled_drivers=enabled_drivers,
                          **kwargs)
