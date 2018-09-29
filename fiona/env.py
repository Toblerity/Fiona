"""Rasterio's GDAL/AWS environment"""

from functools import wraps
import logging
import threading

from fiona._env import (
    GDALEnv, get_gdal_config, set_gdal_config)
from fiona.errors import EnvError
from fiona.session import Session, AWSSession, DummySession


class ThreadEnv(threading.local):
    def __init__(self):
        self._env = None  # Initialises in each thread

        # When the outermost 'rasterio.Env()' executes '__enter__' it
        # probes the GDAL environment to see if any of the supplied
        # config options already exist, the assumption being that they
        # were set with 'osgeo.gdal.SetConfigOption()' or possibly
        # 'rasterio.env.set_gdal_config()'.  The discovered options are
        # reinstated when the outermost Rasterio environment exits.
        # Without this check any environment options that are present in
        # the GDAL environment and are also passed to 'rasterio.Env()'
        # will be unset when 'rasterio.Env()' tears down, regardless of
        # their value.  For example:
        #
        #   from osgeo import gdal import rasterio
        #
        #   gdal.SetConfigOption('key', 'value')
        #   with rasterio.Env(key='something'):
        #       pass
        #
        # The config option 'key' would be unset when 'Env()' exits.
        # A more comprehensive solution would also leverage
        # https://trac.osgeo.org/gdal/changeset/37273 but this gets
        # Rasterio + older versions of GDAL halfway there.  One major
        # assumption is that environment variables are not set directly
        # with 'osgeo.gdal.SetConfigOption()' OR
        # 'rasterio.env.set_gdal_config()' inside of a 'rasterio.Env()'.
        self._discovered_options = None


local = ThreadEnv()

log = logging.getLogger(__name__)


class Env(object):
    """Abstraction for GDAL and AWS configuration

    The GDAL library is stateful: it has a registry of format drivers,
    an error stack, and dozens of configuration options.

    Rasterio's approach to working with GDAL is to wrap all the state
    up using a Python context manager (see PEP 343,
    https://www.python.org/dev/peps/pep-0343/). When the context is
    entered GDAL drivers are registered, error handlers are
    configured, and configuration options are set. When the context
    is exited, drivers are removed from the registry and other
    configurations are removed.

    Example:

        with rasterio.Env(GDAL_CACHEMAX=512) as env:
            # All drivers are registered, GDAL's raster block cache
            # size is set to 512MB.
            # Commence processing...
            ...
            # End of processing.

        # At this point, configuration options are set to their
        # previous (possible unset) values.

    A boto3 session or boto3 session constructor arguments
    `aws_access_key_id`, `aws_secret_access_key`, `aws_session_token`
    may be passed to Env's constructor. In the latter case, a session
    will be created as soon as needed. AWS credentials are configured
    for GDAL as needed.
    """

    @classmethod
    def default_options(cls):
        """Default configuration options

        Parameters
        ----------
        None

        Returns
        -------
        dict
        """
        return {
            'CHECK_WITH_INVERT_PROJ': True,
            'GTIFF_IMPLICIT_JPEG_OVR': False,
            "RASTERIO_ENV": True
        }

    def __init__(
            self, session=None, aws_unsigned=False, aws_access_key_id=None,
            aws_secret_access_key=None, aws_session_token=None,
            region_name=None, profile_name=None, session_class=AWSSession,
            **options):
        """Create a new GDAL/AWS environment.

        Note: this class is a context manager. GDAL isn't configured
        until the context is entered via `with rasterio.Env():`

        Parameters
        ----------
        session : optional
            A Session object.
        aws_unsigned : bool, optional (default: False)
            If True, requests will be unsigned.
        aws_access_key_id : str, optional
            An access key id, as per boto3.
        aws_secret_access_key : str, optional
            A secret access key, as per boto3.
        aws_session_token : str, optional
            A session token, as per boto3.
        region_name : str, optional
            A region name, as per boto3.
        profile_name : str, optional
            A shared credentials profile name, as per boto3.
        session_class : Session, optional
            A sub-class of Session.
        **options : optional
            A mapping of GDAL configuration options, e.g.,
            `CPL_DEBUG=True, CHECK_WITH_INVERT_PROJ=False`.

        Returns
        -------
        Env

        Notes
        -----
        We raise EnvError if the GDAL config options
        AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY are given. AWS
        credentials are handled exclusively by boto3.

        Examples
        --------

        >>> with Env(CPL_DEBUG=True, CPL_CURL_VERBOSE=True):
        ...     with rasterio.open("https://example.com/a.tif") as src:
        ...         print(src.profile)

        For access to secured cloud resources, a Rasterio Session or a
        foreign session object may be passed to the constructor.

        >>> import boto3
        >>> from rasterio.session import AWSSession
        >>> boto3_session = boto3.Session(...)
        >>> with Env(AWSSession(boto3_session)):
        ...     with rasterio.open("s3://mybucket/a.tif") as src:
        ...         print(src.profile)

        """
        if ('AWS_ACCESS_KEY_ID' in options or
                'AWS_SECRET_ACCESS_KEY' in options):
            raise EnvError(
                "GDAL's AWS config options can not be directly set. "
                "AWS credentials are handled exclusively by boto3.")

        if session:
            self.session = session
        else:
            self.session = DummySession()

        self.options = options.copy()
        self.context_options = {}

    @classmethod
    def from_defaults(cls, *args, **kwargs):
        """Create an environment with default config options

        Parameters
        ----------
        args : optional
            Positional arguments for Env()
        kwargs : optional
            Keyword arguments for Env()

        Returns
        -------
        Env

        Notes
        -----
        The items in kwargs will be overlaid on the default values.

        """
        options = Env.default_options()
        options.update(**kwargs)
        return Env(*args, **options)

    @property
    def is_credentialized(self):
        """Test for existence of cloud credentials

        Returns
        -------
        bool
        """
        return hascreds()  # bool(self.session)

    def credentialize(self):
        """Get credentials and configure GDAL

        Note well: this method is a no-op if the GDAL environment
        already has credentials, unless session is not None.

        Returns
        -------
        None

        """
        if hascreds():
            pass
        else:
            cred_opts = self.session.get_credential_options()
            self.options.update(**cred_opts)
            setenv(**cred_opts)

    def drivers(self):
        """Return a mapping of registered drivers."""
        return local._env.drivers()

    def __enter__(self):
        log.debug("Entering env context: %r", self)
        if local._env is None:
            log.debug("Starting outermost env")
            self._has_parent_env = False

            # See note directly above where _discovered_options is globally
            # defined.  This MUST happen before calling 'defenv()'.
            local._discovered_options = {}
            # Don't want to reinstate the "RASTERIO_ENV" option.
            probe_env = {k for k in self.options.keys() if k != "RASTERIO_ENV"}
            for key in probe_env:
                val = get_gdal_config(key, normalize=False)
                if val is not None:
                    local._discovered_options[key] = val
                    log.debug("Discovered option: %s=%s", key, val)

            defenv(**self.options)
            self.context_options = {}
        else:
            self._has_parent_env = True
            self.context_options = getenv()
            setenv(**self.options)

        self.credentialize()

        log.debug("Entered env context: %r", self)
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        log.debug("Exiting env context: %r", self)
        delenv()
        if self._has_parent_env:
            defenv()
            setenv(**self.context_options)
        else:
            log.debug("Exiting outermost env")
            # See note directly above where _discovered_options is globally
            # defined.
            while local._discovered_options:
                key, val = local._discovered_options.popitem()
                set_gdal_config(key, val, normalize=False)
                log.debug(
                    "Set discovered option back to: '%s=%s", key, val)
            local._discovered_options = None
        log.debug("Exited env context: %r", self)


def defenv(**options):
    """Create a default environment if necessary."""
    if local._env:
        log.debug("GDAL environment exists: %r", local._env)
    else:
        log.debug("No GDAL environment exists")
        local._env = GDALEnv()
        local._env.update_config_options(**options)
        log.debug(
            "New GDAL environment %r created", local._env)
    local._env.start()


def getenv():
    """Get a mapping of current options."""
    if not local._env:
        raise EnvError("No GDAL environment exists")
    else:
        log.debug("Got a copy of environment %r options", local._env)
        return local._env.options.copy()


def hasenv():
    return bool(local._env)


def setenv(**options):
    """Set options in the existing environment."""
    if not local._env:
        raise EnvError("No GDAL environment exists")
    else:
        local._env.update_config_options(**options)
        log.debug("Updated existing %r with options %r", local._env, options)


def hascreds():
    gdal_config = local._env.get_config_options()
    return bool('AWS_ACCESS_KEY_ID' in gdal_config and
                'AWS_SECRET_ACCESS_KEY' in gdal_config)


def delenv():
    """Delete options in the existing environment."""
    if not local._env:
        raise EnvError("No GDAL environment exists")
    else:
        local._env.clear_config_options()
        log.debug("Cleared existing %r options", local._env)
    local._env.stop()
    local._env = None


def ensure_env(f):
    """A decorator that ensures an env exists before a function
    calls any GDAL C functions."""
    @wraps(f)
    def wrapper(*args, **kwds):
        if local._env:
            return f(*args, **kwds)
        else:
            with Env.from_defaults():
                return f(*args, **kwds)
    return wrapper


def ensure_env_with_credentials(f):
    """Ensures a config environment exists and has credentials.

    Parameters
    ----------
    f : function
        A function.

    Returns
    -------
    A function wrapper.

    Notes
    -----
    The function wrapper checks the first argument of f and
    credentializes the environment if the first argument is a URI with
    scheme "s3".

    """
    @wraps(f)
    def wrapper(*args, **kwds):
        if local._env:
            env_ctor = Env
        else:
            env_ctor = Env.from_defaults

        if isinstance(args[0], str):
            session = Session.from_path(args[0])
        else:
            session = Session.from_path(None)

        with env_ctor(session=session):
            log.debug("Credentialized: {!r}".format(getenv()))
            return f(*args, **kwds)

    return wrapper
