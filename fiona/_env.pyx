# cython: c_string_type=unicode, c_string_encoding=utf8
"""GDAL and OGR driver and configuration management

The main thread always utilizes CPLSetConfigOption. Child threads
utilize CPLSetThreadLocalConfigOption instead. All threads use
CPLGetConfigOption and not CPLGetThreadLocalConfigOption, thus child
threads will inherit config options from the main thread unless the
option is set to a new value inside the thread.
"""

include "gdal.pxi"

from collections import namedtuple
import logging
import os
import os.path
import sys
import threading


level_map = {
    0: 0,
    1: logging.DEBUG,
    2: logging.WARNING,
    3: logging.ERROR,
    4: logging.CRITICAL }

code_map = {
    0: 'CPLE_None',
    1: 'CPLE_AppDefined',
    2: 'CPLE_OutOfMemory',
    3: 'CPLE_FileIO',
    4: 'CPLE_OpenFailed',
    5: 'CPLE_IllegalArg',
    6: 'CPLE_NotSupported',
    7: 'CPLE_AssertionFailed',
    8: 'CPLE_NoWriteAccess',
    9: 'CPLE_UserInterrupt',
    10: 'ObjectNull',

    # error numbers 11-16 are introduced in GDAL 2.1. See
    # https://github.com/OSGeo/gdal/pull/98.
    11: 'CPLE_HttpResponse',
    12: 'CPLE_AWSBucketNotFound',
    13: 'CPLE_AWSObjectNotFound',
    14: 'CPLE_AWSAccessDenied',
    15: 'CPLE_AWSInvalidCredentials',
    16: 'CPLE_AWSSignatureDoesNotMatch'}


log = logging.getLogger(__name__)


cdef bint is_64bit = sys.maxsize > 2 ** 32


def calc_gdal_version_num(maj, min, rev):
    """Calculates the internal gdal version number based on major, minor and revision

    GDAL Version Information macro changed with GDAL version 1.10.0 (April 2013)

    """
    if (maj, min, rev) >= (1, 10, 0):
        return int(maj * 1000000 + min * 10000 + rev * 100)
    else:
        return int(maj * 1000 + min * 100 + rev * 10)


def get_gdal_version_num():
    """Return current internal version number of gdal"""
    return int(GDALVersionInfo("VERSION_NUM"))


def get_gdal_release_name():
    """Return release name of gdal"""
    cdef const char *name_c = NULL
    name_c = GDALVersionInfo("RELEASE_NAME")
    name = name_c
    return name


GDALVersion = namedtuple("GDALVersion", ["major", "minor", "revision"])


def get_gdal_version_tuple():
    """
    Calculates gdal version tuple from gdal's internal version number.

    GDAL Version Information macro changed with GDAL version 1.10.0 (April 2013)
    """
    gdal_version_num = get_gdal_version_num()

    if gdal_version_num >= calc_gdal_version_num(1, 10, 0):
        major = gdal_version_num // 1000000
        minor = (gdal_version_num - (major * 1000000)) // 10000
        revision = (gdal_version_num - (major * 1000000) - (minor * 10000)) // 100
        return GDALVersion(major, minor, revision)
    else:
        major = gdal_version_num // 1000
        minor = (gdal_version_num - (major * 1000)) // 100
        revision = (gdal_version_num - (major * 1000) - (minor * 100)) // 10
        return GDALVersion(major, minor, revision)


cdef void log_error(CPLErr err_class, int err_no, const char* msg) with gil:
    """Send CPL debug messages and warnings to Python's logger."""
    log = logging.getLogger(__name__)
    if err_no in code_map:
        log.log(level_map[err_class], "%s", msg)
    else:
        log.info("Unknown error number %r.", err_no)


# Definition of GDAL callback functions, one for Windows and one for
# other platforms. Each calls log_error().
IF UNAME_SYSNAME == "Windows":
    cdef void __stdcall logging_error_handler(CPLErr err_class, int err_no,
                                              const char* msg) with gil:
        log_error(err_class, err_no, msg)
ELSE:
    cdef void logging_error_handler(CPLErr err_class, int err_no,
                                    const char* msg) with gil:
        log_error(err_class, err_no, msg)


def driver_count():
    """Return the count of all drivers"""
    return GDALGetDriverCount() + OGRGetDriverCount()


cpdef get_gdal_config(key, normalize=True):
    """Get the value of a GDAL configuration option.  When requesting
    ``GDAL_CACHEMAX`` the value is returned unaltered. 

    Parameters
    ----------
    key : str
        Name of config option.
    normalize : bool, optional
        Convert values of ``"ON"'`` and ``"OFF"`` to ``True`` and ``False``.
    """
    key = key.encode('utf-8')

    # GDAL_CACHEMAX is a special case
    if key.lower() == b'gdal_cachemax':
        if is_64bit:
            return GDALGetCacheMax64()
        else:
            return GDALGetCacheMax()
    else:
        val = CPLGetConfigOption(<const char *>key, NULL)

    if not val:
        return None
    elif not normalize:
        return val
    elif val.isdigit():
        return int(val)
    else:
        if val == u'ON':
            return True
        elif val == u'OFF':
            return False
        else:
            return val


cpdef set_gdal_config(key, val, normalize=True):
    """Set a GDAL configuration option's value.

    Parameters
    ----------
    key : str
        Name of config option.
    normalize : bool, optional
        Convert ``True`` to `"ON"` and ``False`` to `"OFF"``.
    """
    key = key.encode('utf-8')

    # GDAL_CACHEMAX is a special case
    if key.lower() == b'gdal_cachemax':
        if is_64bit:
            GDALSetCacheMax64(val)
        else:
            GDALSetCacheMax(val)
        return
    elif normalize and isinstance(val, bool):
        val = ('ON' if val and val else 'OFF').encode('utf-8')
    else:
        # Value could be an int
        val = str(val).encode('utf-8')

    if isinstance(threading.current_thread(), threading._MainThread):
        CPLSetConfigOption(<const char *>key, <const char *>val)
    else:
        CPLSetThreadLocalConfigOption(<const char *>key, <const char *>val)


cpdef del_gdal_config(key):
    """Delete a GDAL configuration option.

    Parameters
    ----------
    key : str
        Name of config option.
    """
    key = key.encode('utf-8')
    if isinstance(threading.current_thread(), threading._MainThread):
        CPLSetConfigOption(<const char *>key, NULL)
    else:
        CPLSetThreadLocalConfigOption(<const char *>key, NULL)


cdef class ConfigEnv(object):
    """Configuration option management"""

    def __init__(self, **options):
        self.options = options.copy()
        self.update_config_options(**self.options)

    def update_config_options(self, **kwargs):
        """Update GDAL config options."""
        for key, val in kwargs.items():
            set_gdal_config(key, val)
            self.options[key] = val

    def clear_config_options(self):
        """Clear GDAL config options."""
        while self.options:
            key, val = self.options.popitem()
            del_gdal_config(key)

    def get_config_options(self):
        return {k: get_gdal_config(k) for k in self.options}


class GDALDataFinder(object):
    """Finds GDAL data files

    Note: this class is private in 1.8.x and not in the public API.

    """

    def search(self, prefix=None):
        """Returns GDAL_DATA location"""
        path = self.search_wheel(prefix or __file__)
        if not path:
            path = self.search_prefix(prefix or sys.prefix)
            if not path:
                path = self.search_debian(prefix or sys.prefix)
        return path

    def search_wheel(self, prefix=None):
        """Check wheel location"""
        if prefix is None:
            prefix = __file__
        datadir = os.path.abspath(os.path.join(os.path.dirname(prefix), "gdal_data"))
        return datadir if os.path.exists(os.path.join(datadir, 'pcs.csv')) else None

    def search_prefix(self, prefix=sys.prefix):
        """Check sys.prefix location"""
        datadir = os.path.join(prefix, 'share', 'gdal')
        return datadir if os.path.exists(os.path.join(datadir, 'pcs.csv')) else None

    def search_debian(self, prefix=sys.prefix):
        """Check Debian locations"""
        gdal_version = get_gdal_version_tuple()
        datadir = os.path.join(prefix, 'share', 'gdal', '{}.{}'.format(gdal_version.major, gdal_version.minor))
        return datadir if os.path.exists(os.path.join(datadir, 'pcs.csv')) else None


class PROJDataFinder(object):
    """Finds PROJ data files

    Note: this class is private in 1.8.x and not in the public API.

    """

    def search(self, prefix=None):
        """Returns PROJ_LIB location"""
        path = self.search_wheel(prefix or __file__)
        if not path:
            path = self.search_prefix(prefix or sys.prefix)
        return path

    def search_wheel(self, prefix=None):
        """Check wheel location"""
        if prefix is None:
            prefix = __file__
        datadir = os.path.abspath(os.path.join(os.path.dirname(prefix), "proj_data"))
        return datadir if os.path.exists(datadir) else None

    def search_prefix(self, prefix=sys.prefix):
        """Check sys.prefix location"""
        datadir = os.path.join(prefix, 'share', 'proj')
        return datadir if os.path.exists(datadir) else None


cdef class GDALEnv(ConfigEnv):
    """Configuration and driver management"""

    def __init__(self, **options):
        super(GDALEnv, self).__init__(**options)
        self._have_registered_drivers = False

    def start(self):
        CPLPushErrorHandler(<CPLErrorHandler>logging_error_handler)
        log.debug("Logging error handler pushed.")

        # The outer if statement prevents each thread from acquiring a
        # lock when the environment starts, and the inner avoids a
        # potential race condition.
        if not self._have_registered_drivers:
            with threading.Lock():
                if not self._have_registered_drivers:

                    GDALAllRegister()
                    OGRRegisterAll()
                    log.debug("All drivers registered.")

                    if 'GDAL_DATA' in os.environ:
                        self.update_config_options(GDAL_DATA=os.environ['GDAL_DATA'])
                        log.debug("GDAL_DATA found in environment: %r.", os.environ['GDAL_DATA'])

                    else:
                        path = GDALDataFinder().search()

                        if path:
                            self.update_config_options(GDAL_DATA=path)
                            log.debug("GDAL_DATA not found in environment, set to %r.", path)

                    if 'PROJ_LIB' not in os.environ:

                        path = PROJDataFinder().search()

                        if path:
                            os.environ['PROJ_LIB'] = path
                            log.debug("PROJ data not found in environment, set to %r.", path)

                    if driver_count() == 0:
                        CPLPopErrorHandler()
                        log.debug("Error handler popped")
                        raise ValueError("Drivers not registered.")

                    # Flag the drivers as registered, otherwise every thread
                    # will acquire a threadlock every time a new environment
                    # is started rather than just whenever the first thread
                    # actually makes it this far.
                    self._have_registered_drivers = True

        log.debug("Started GDALEnv %r.", self)

    def stop(self):
        # NB: do not restore the CPL error handler to its default
        # state here. If you do, log messages will be written to stderr
        # by GDAL instead of being sent to Python's logging module.
        log.debug("Stopping GDALEnv %r.", self)
        CPLPopErrorHandler()
        log.debug("Error handler popped.")
        log.debug("Stopped GDALEnv %r.", self)

    def drivers(self):
        cdef OGRSFDriverH driver = NULL
        cdef int i

        result = {}
        for i in range(OGRGetDriverCount()):
            drv = OGRGetDriver(i)
            key = <char *>OGR_Dr_GetName(drv)
            val = <char *>OGR_Dr_GetName(drv)
            result[key] = val

        return result
