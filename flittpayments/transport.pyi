from types import TracebackType
from typing import Any, Awaitable, Generic, Optional, Type, TypeVar

from flittpayments._types import Headers, Response, Timeout

_ResultT_co = TypeVar('_ResultT_co', covariant=True)


class BaseTransport(Generic[_ResultT_co]):
    def request(
        self,
        method: str,
        url: str,
        data: Optional[str] = ...,
        headers: Optional[Headers] = ...,
        timeout: Optional[Timeout] = ...,
    ) -> Any: ...


class SyncTransport(BaseTransport[Response]):
    session: Any

    def __init__(self, session: Any = ...) -> None: ...
    def request(
        self,
        method: str,
        url: str,
        data: Optional[str] = ...,
        headers: Optional[Headers] = ...,
        timeout: Optional[Timeout] = ...,
    ) -> Any: ...
    def close(self) -> Any: ...
    def __enter__(self) -> SyncTransport: ...
    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None: ...


class AsyncTransport(BaseTransport[Awaitable[Response]]):
    client: Any

    def __init__(self, client: Any = ..., **client_options: Any) -> None: ...
    def request(
        self,
        method: str,
        url: str,
        data: Optional[str] = ...,
        headers: Optional[Headers] = ...,
        timeout: Optional[Timeout] = ...,
    ) -> Awaitable[Any]: ...
    def aclose(self) -> Awaitable[None]: ...
    def __aenter__(self) -> Awaitable[AsyncTransport]: ...
    def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Awaitable[Optional[bool]]: ...
