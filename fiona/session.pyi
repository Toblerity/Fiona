from boto3.session import Session
from typing import (
    Any,
    Dict,
    Optional,
    Type,
    Union,
)


class AWSSession:
    def __init__(
        self,
        session: Optional[Session] = ...,
        aws_unsigned: bool = ...,
        aws_access_key_id: Optional[str] = ...,
        aws_secret_access_key: Optional[str] = ...,
        aws_session_token: None = ...,
        region_name: Optional[str] = ...,
        profile_name: Optional[str] = ...,
        endpoint_url: Optional[str] = ...,
        requester_pays: bool = ...
    ) -> None: ...
    @property
    def credentials(self) -> Dict[str, str]: ...
    def get_credential_options(self) -> Dict[str, str]: ...
    @classmethod
    def hascreds(cls, config: Dict[str, str]) -> bool: ...


class AzureSession:
    def __init__(
        self,
        azure_storage_connection_string: Optional[str] = ...,
        azure_storage_account: Optional[str] = ...,
        azure_storage_access_key: Optional[str] = ...,
        azure_unsigned: bool = ...
    ) -> None: ...
    @property
    def credentials(self) -> Dict[str, str]: ...
    def get_credential_options(self) -> Dict[str, str]: ...


class DummySession:
    def __init__(self, *args, **kwargs) -> None: ...
    def get_credential_options(self) -> Dict[Any, Any]: ...
    @classmethod
    def hascreds(cls, config: Dict[str, Union[bool, str]]) -> bool: ...


class GSSession:
    def __init__(self, google_application_credentials: Optional[str] = ...) -> None: ...
    @property
    def credentials(self) -> Dict[str, str]: ...
    def get_credential_options(self) -> Dict[str, str]: ...
    @classmethod
    def hascreds(cls, config: Dict[str, str]) -> bool: ...


class OSSSession:
    def __init__(
        self,
        oss_access_key_id: Optional[str] = ...,
        oss_secret_access_key: Optional[str] = ...,
        oss_endpoint: Optional[str] = ...
    ) -> None: ...
    @property
    def credentials(self) -> Dict[str, Optional[str]]: ...
    def get_credential_options(self) -> Dict[str, Optional[str]]: ...


class Session:
    @staticmethod
    def aws_or_dummy(*args, **kwargs) -> Union[AWSSession, DummySession]: ...
    @staticmethod
    def cls_from_path(
        path: str
    ) -> Union[Type[OSSSession], Type[DummySession], Type[AWSSession], Type[AzureSession]]: ...
    @staticmethod
    def from_foreign_session(
        session: Optional[Session],
        cls: Optional[Type[AWSSession]] = ...
    ) -> Union[AWSSession, DummySession]: ...
    @staticmethod
    def from_path(
        path: str,
        *args,
        **kwargs
    ) -> Union[AWSSession, AzureSession, OSSSession, DummySession]: ...
    def get_credential_options(self) -> NotImplementedType: ...
    @classmethod
    def hascreds(cls, config: Dict[Any, Any]) -> NotImplementedType: ...


class SwiftSession:
    def __init__(
        self,
        session: None = ...,
        swift_storage_url: Optional[str] = ...,
        swift_auth_token: Optional[str] = ...,
        swift_auth_v1_url: None = ...,
        swift_user: None = ...,
        swift_key: None = ...
    ) -> None: ...
    @property
    def credentials(self) -> Dict[str, str]: ...
    def get_credential_options(self) -> Dict[str, str]: ...
