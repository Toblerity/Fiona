"""fiona._err

Transformation of GDAL C API errors to Python exceptions using Python's
``with`` statement and an error-handling context manager class.

The ``cpl_errs`` error-handling context manager is intended for use in
Rasterio's Cython code. When entering the body of a ``with`` statement,
the context manager clears GDAL's error stack. On exit, the context
manager pops the last error off the stack and raises an appropriate
Python exception. It's otherwise pretty difficult to do this kind of
thing.  I couldn't make it work with a CPL error handler, Cython's
C code swallows exceptions raised from C callbacks.

When used to wrap a call to open a PNG in update mode

    with cpl_errs:
        cdef void *hds = GDALOpen('file.png', 1)
    if hds == NULL:
        raise ValueError("NULL dataset")

the ValueError of last resort never gets raised because the context
manager raises a more useful and informative error:

    Traceback (most recent call last):
      File "/Users/sean/code/rasterio/scripts/rio_insp", line 65, in <module>
        with rasterio.open(args.src, args.mode) as src:
      File "/Users/sean/code/rasterio/rasterio/__init__.py", line 111, in open
        s.start()
    ValueError: The PNG driver does not support update access to existing datasets.
"""

from __future__ import absolute_import

# CPL function declarations.
cdef extern from "cpl_error.h":

    ctypedef enum CPLErr:
        CE_None
        CE_Debug
        CE_Warning
        CE_Failure
        CE_Fatal

    int CPLGetLastErrorNo()
    const char* CPLGetLastErrorMsg()
    int CPLGetLastErrorType()
    void CPLErrorReset()


from enum import IntEnum

# Python exceptions expressing the CPL error numbers.

class CPLE_BaseError(Exception):
    """Base CPL error class
    Exceptions deriving from this class are intended for use only in
    Rasterio's Cython code. Let's not expose API users to them.
    """

    def __init__(self, error, errno, errmsg):
        self.error = error
        self.errno = errno
        self.errmsg = errmsg

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u"{}".format(self.errmsg)

    @property
    def args(self):
        return self.error, self.errno, self.errmsg


class CPLE_AppDefinedError(CPLE_BaseError):
    pass


class CPLE_OutOfMemoryError(CPLE_BaseError):
    pass


class CPLE_FileIOError(CPLE_BaseError):
    pass


class CPLE_OpenFailedError(CPLE_BaseError):
    pass


class CPLE_IllegalArgError(CPLE_BaseError):
    pass


class CPLE_NotSupportedError(CPLE_BaseError):
    pass


class CPLE_AssertionFailedError(CPLE_BaseError):
    pass


class CPLE_NoWriteAccessError(CPLE_BaseError):
    pass


class CPLE_UserInterruptError(CPLE_BaseError):
    pass


class ObjectNullError(CPLE_BaseError):
    pass


class CPLE_HttpResponseError(CPLE_BaseError):
    pass


class CPLE_AWSBucketNotFoundError(CPLE_BaseError):
    pass


class CPLE_AWSObjectNotFoundError(CPLE_BaseError):
    pass


class CPLE_AWSAccessDeniedError(CPLE_BaseError):
    pass


class CPLE_AWSInvalidCredentialsError(CPLE_BaseError):
    pass


class CPLE_AWSSignatureDoesNotMatchError(CPLE_BaseError):
    pass


class FionaNullPointerError(CPLE_BaseError):
    """
    Returned from exc_wrap_pointer when a NULL pointer is passed, but no GDAL
    error was raised.
    """
    pass


class FionaCPLError(CPLE_BaseError):
    """
    Returned from exc_wrap_int when a error code is returned, but no GDAL
    error was set.
    """
    pass


# Map of GDAL error numbers to the Python exceptions.
exception_map = {
    1: CPLE_AppDefinedError,
    2: CPLE_OutOfMemoryError,
    3: CPLE_FileIOError,
    4: CPLE_OpenFailedError,
    5: CPLE_IllegalArgError,
    6: CPLE_NotSupportedError,
    7: CPLE_AssertionFailedError,
    8: CPLE_NoWriteAccessError,
    9: CPLE_UserInterruptError,
    10: ObjectNullError,

    # error numbers 11-16 are introduced in GDAL 2.1. See
    # https://github.com/OSGeo/gdal/pull/98.
    11: CPLE_HttpResponseError,
    12: CPLE_AWSBucketNotFoundError,
    13: CPLE_AWSObjectNotFoundError,
    14: CPLE_AWSAccessDeniedError,
    15: CPLE_AWSInvalidCredentialsError,
    16: CPLE_AWSSignatureDoesNotMatchError}


# CPL Error types as an enum.
class GDALError(IntEnum):
    none = CE_None
    debug = CE_Debug
    warning = CE_Warning
    failure = CE_Failure
    fatal = CE_Fatal


cdef class GDALErrCtxManager:
    """A manager for GDAL error handling contexts."""

    def __enter__(self):
        CPLErrorReset()
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        cdef int err_type = CPLGetLastErrorType()
        cdef int err_no = CPLGetLastErrorNo()
        cdef const char *msg = CPLGetLastErrorMsg()
        # TODO: warn for err_type 2?
        if err_type >= 2:
            raise exception_map[err_no](err_type, err_no, msg)


cdef inline object exc_check():
    """Checks GDAL error stack for fatal or non-fatal errors

    Returns
    -------
    An Exception, SystemExit, or None
    """
    cdef const char *msg_c = NULL

    err_type = CPLGetLastErrorType()
    err_no = CPLGetLastErrorNo()
    err_msg = CPLGetLastErrorMsg()

    if err_msg == NULL:
        msg = "No error message."
    else:
        # Reformat messages.
        msg_b = err_msg
        msg = msg_b.decode('utf-8')
        msg = msg.replace("`", "'")
        msg = msg.replace("\n", " ")

    if err_type == 3:
        CPLErrorReset()
        return exception_map.get(
            err_no, CPLE_BaseError)(err_type, err_no, msg)

    if err_type == 4:
        return SystemExit("Fatal error: {0}".format((err_type, err_no, msg)))

    else:
        return


cdef get_last_error_msg():
    """Checks GDAL error stack for the latest error message
    Returns
    -------
    An error message or empty string
    """

    err_msg = CPLGetLastErrorMsg()

    if err_msg != NULL:
        # Reformat messages.
        msg_b = err_msg
        msg = msg_b.decode('utf-8')
        msg = msg.replace("`", "'")
        msg = msg.replace("\n", " ")
    else:
        msg = ""

    return msg


cdef int exc_wrap_int(int err) except -1:
    """Wrap a GDAL/OGR function that returns CPLErr or OGRErr (int)

    Raises a Rasterio exception if a non-fatal error has be set.
    """
    if err:
        exc = exc_check()
        if exc:
            raise exc
        else:
            raise FionaCPLError(-1, -1, "The wrapped function returned an error code, but no error message was set.")
    return err


cdef OGRErr exc_wrap_ogrerr(OGRErr err) except -1:
    """Wrap a function that returns OGRErr but does not use the
    CPL error stack.

    """
    if err == 0:
        return err
    else:
        raise CPLE_BaseError(3, err, "OGR Error code {}".format(err))


cdef void *exc_wrap_pointer(void *ptr) except NULL:
    """Wrap a GDAL/OGR function that returns GDALDatasetH etc (void *)
    Raises a Rasterio exception if a non-fatal error has be set.
    """
    if ptr == NULL:
        exc = exc_check()
        if exc:
            raise exc
        else:
            # null pointer was passed, but no error message from GDAL
            raise FionaNullPointerError(-1, -1, "NULL pointer error")
    return ptr


cdef VSILFILE *exc_wrap_vsilfile(VSILFILE *f) except NULL:
    """Wrap a GDAL/OGR function that returns GDALDatasetH etc (void *)

    Raises a Rasterio exception if a non-fatal error has be set.
    """
    if f == NULL:
        exc = exc_check()
        if exc:
            raise exc
    return f

cpl_errs = GDALErrCtxManager()
