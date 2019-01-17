"""Abstraction for sessions in various clouds."""


from fiona.path import parse_path, UnparsedPath


class Session(object):
    """Base for classes that configure access to secured resources.

    Attributes
    ----------
    credentials : dict
        Keys and values for session credentials.

    Notes
    -----
    This class is not intended to be instantiated.

    """

    def get_credential_options(self):
        """Get credentials as GDAL configuration options

        Returns
        -------
        dict

        """
        return NotImplementedError

    @staticmethod
    def from_foreign_session(session, cls=None):
        """Create a session object matching the foreign `session`.

        Parameters
        ----------
        session : obj
            A foreign session object.
        cls : Session class, optional
            The class to return.

        Returns
        -------
        Session

        """
        if not cls:
            return DummySession()
        else:
            return cls(session)

    @staticmethod
    def from_path(path, *args, **kwargs):
        """Create a session object suited to the data at `path`.

        Parameters
        ----------
        path : str
            A dataset path or identifier.
        args : sequence
            Positional arguments for the foreign session constructor.
        kwargs : dict
            Keyword arguments for the foreign session constructor.

        Returns
        -------
        Session

        """
        if not path:
            return DummySession()

        path = parse_path(path)

        if isinstance(path, UnparsedPath) or path.is_local:
            return DummySession()

        elif path.scheme == "s3" or path.scheme.endswith("+s3") or "amazonaws.com" in path.path:
            return AWSSession(*args, **kwargs)

        # This factory can be extended to other cloud providers here.
        # elif path.scheme == "cumulonimbus":  # for example.
        #     return CumulonimbusSession(*args, **kwargs)

        else:
            return DummySession()


class DummySession(Session):
    """A dummy session.

    Attributes
    ----------
    credentials : dict
        The session credentials.

    """

    def __init__(self, *args, **kwargs):
        self._session = None
        self.credentials = {}

    def get_credential_options(self):
        """Get credentials as GDAL configuration options

        Returns
        -------
        dict

        """
        return {}


class AWSSession(Session):
    """Configures access to secured resources stored in AWS S3.
    """

    def __init__(
            self, session=None, aws_unsigned=False, aws_access_key_id=None,
            aws_secret_access_key=None, aws_session_token=None,
            region_name=None, profile_name=None, requester_pays=False):
        """Create a new boto3 session

        Parameters
        ----------
        session : optional
            A boto3 session object.
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
        requester_pays : bool, optional
            True if the requester agrees to pay transfer costs (default:
            False)
        """
        import boto3

        if session:
            self._session = session
        else:
            self._session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
                region_name=region_name,
                profile_name=profile_name)

        self.requester_pays = requester_pays
        self.unsigned = aws_unsigned
        self._creds = self._session._session.get_credentials()

    @property
    def credentials(self):
        """The session credentials as a dict"""
        creds = {}
        if self._creds:
            if self._creds.access_key:  # pragma: no branch
                creds['aws_access_key_id'] = self._creds.access_key
            if self._creds.secret_key:  # pragma: no branch
                creds['aws_secret_access_key'] = self._creds.secret_key
            if self._creds.token:
                creds['aws_session_token'] = self._creds.token
        if self._session.region_name:
            creds['aws_region'] = self._session.region_name
        if self.requester_pays:
            creds['aws_request_payer'] = 'requester'
        return creds

    def get_credential_options(self):
        """Get credentials as GDAL configuration options

        Returns
        -------
        dict

        """
        if self.unsigned:
            return {'AWS_NO_SIGN_REQUEST': 'YES'}
        else:
            return {k.upper(): v for k, v in self.credentials.items()}

class GSSession(Session):
    """Configures access to secured resources stored in Google Cloud Storage
    """
    def __init__(self, google_application_credentials=None):
        """Create new Google Cloude Storage session

        Parameters
        ----------
        google_application_credentials: string
            Path to the google application credentials JSON file.
        """

        self._creds = {}
        if google_application_credentials is not None:
            self._creds['google_application_credentials'] = google_application_credentials

    @classmethod
    def hascreds(cls, config):
        """Determine if the given configuration has proper credentials

        Parameters
        ----------
        cls : class
            A Session class.
        config : dict
            GDAL configuration as a dict.

        Returns
        -------
        bool

        """
        return 'GOOGLE_APPLICATION_CREDENTIALS' in config

    @property
    def credentials(self):
        """The session credentials as a dict"""
        return self._creds

    def get_credential_options(self):
        """Get credentials as GDAL configuration options

        Returns
        -------
        dict

        """
        return {k.upper(): v for k, v in self.credentials.items()}
