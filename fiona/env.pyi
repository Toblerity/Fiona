from boto3.session import Session
from fiona.session import (
    AWSSession,
    DummySession,
    GSSession,
)
from typing import (
    Callable,
    Dict,
    Optional,
    Union,
)


def defenv(**options) -> None: ...


def delenv() -> None: ...


def ensure_env(f: Callable) -> Callable: ...


def ensure_env_with_credentials(f: Callable) -> Callable: ...


def env_ctx_if_needed() -> Union[NullContextManager, Env]: ...


def getenv() -> Dict[str, Union[str, bool]]: ...


def hasenv() -> bool: ...


def setenv(**options) -> None: ...


class Env:
    def __enter__(self) -> Env: ...
    def __exit__(self, exc_type: None = ..., exc_val: None = ..., exc_tb: None = ...) -> None: ...
    def __init__(
        self,
        session: Optional[Union[GSSession, AWSSession, DummySession, Session]] = ...,
        aws_unsigned: bool = ...,
        profile_name: None = ...,
        session_class: Callable = ...,
        **options
    ) -> None: ...
    def credentialize(self) -> None: ...
    @classmethod
    def default_options(cls) -> Dict[str, bool]: ...
    @classmethod
    def from_defaults(cls, *args, **kwargs) -> Env: ...


class GDALVersion:
    def at_least(self, other: str) -> bool: ...
    @classmethod
    def parse(cls, input: str) -> GDALVersion: ...
    @classmethod
    def runtime(cls) -> GDALVersion: ...


class NullContextManager:
    def __enter__(self) -> NullContextManager: ...
    def __exit__(self, *args) -> None: ...
    def __init__(self) -> None: ...
