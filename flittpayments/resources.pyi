from typing import Any, Dict, Generic, Optional, TypeVar

from flittpayments._types import Headers
from flittpayments.api import Api

_ResultT = TypeVar('_ResultT')


class Resource(Generic[_ResultT]):
    api: Api[_ResultT]
    order_id: Optional[Any]
    __data__: Dict[str, Any]

    def __init__(
        self,
        api: Api[_ResultT] = ...,
        headers: Optional[Headers] = ...,
    ) -> None: ...
    def __contains__(self, name: str) -> bool: ...
    def get_url(self) -> Optional[Any]: ...
    def response(self, response: Any, order_id: Any = ...) -> _ResultT: ...
