"""Classes capable of reading and writing collections
"""

from collections import OrderedDict
import logging

import fiona._loading
with fiona._loading.add_gdal_dll_directories():
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
    def __init__(self, file_or_bytes=None, filename=None, ext=""):
        if ext and not ext.startswith("."):
            ext = "." + ext
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
        if self.closed:
            raise IOError("I/O operation on closed file.")

        if not self.exists():
            self._ensure_extension(driver)
            this_schema = schema.copy()
            this_schema["properties"] = OrderedDict(schema["properties"])
            return Collection(
                self.name,
                "w",
                crs=crs,
                driver=driver,
                schema=this_schema,
                encoding=encoding,
                layer=layer,
                enabled_drivers=enabled_drivers,
                crs_wkt=crs_wkt,
                **kwargs
            )

        elif self.mode in ("r", "r+"):
            return Collection(
                self.name,
                "r",
                driver=driver,
                encoding=encoding,
                layer=layer,
                enabled_drivers=enabled_drivers,
                **kwargs
            )

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
        super(ZipMemoryFile, self).__init__(file_or_bytes, ext=".zip")

    def open(self, path=None, driver=None, encoding=None, layer=None,
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
        if self.closed:
            raise IOError("I/O operation on closed file.")
        if path:
            vsi_path = '/vsizip{0}/{1}'.format(self.name, path.lstrip('/'))
        else:
            vsi_path = '/vsizip{0}'.format(self.name)

        return Collection(vsi_path, 'r', driver=driver, encoding=encoding,
                          layer=layer, enabled_drivers=enabled_drivers,
                          **kwargs)
