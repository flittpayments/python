from typing import Any, Dict, Generic, Optional, TypeVar, overload

from flittpayments._types import Headers, Response, Timeout
from flittpayments.transport import BaseTransport, SyncTransport

_ResultT = TypeVar('_ResultT')


class Api(Generic[_ResultT]):
    user_agent: str
    merchant_id: Any
    secret_key: str
    request_type: str
    timeout: Timeout
    transport: BaseTransport[_ResultT]
    api_url: str
    api_protocol: str

    @overload
    def __init__(
        self: Api[Response],
        *,
        merchant_id: Any = ...,
        secret_key: str = ...,
        request_type: str = ...,
        api_domain: str = ...,
        api_protocol: str = ...,
        timeout: Timeout = ...,
        transport: None = ...,
        **kwargs: Any
    ) -> None: ...

    @overload
    def __init__(
        self: Api[_ResultT],
        *,
        merchant_id: Any = ...,
        secret_key: str = ...,
        request_type: str = ...,
        api_domain: str = ...,
        api_protocol: str = ...,
        timeout: Timeout = ...,
        transport: BaseTransport[_ResultT],
        **kwargs: Any
    ) -> None: ...

    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = ...,
        headers: Optional[Headers] = ...,
    ) -> Any: ...
    def close(self) -> Any: ...
