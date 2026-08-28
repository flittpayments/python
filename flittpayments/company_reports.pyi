from typing import Generic, TypeVar

from flittpayments._types import RequestData
from flittpayments.api import Api

_ResultT = TypeVar('_ResultT')
DEFAULT_REPORTS_DOMAIN: str


class CompanyReports(Generic[_ResultT]):
    token_path: str
    report_path: str
    api: Api[_ResultT]
    api_domain: str
    api_url: str

    def __init__(
        self,
        api: Api[_ResultT],
        api_domain: str = ...,
    ) -> None: ...
    def get(self, data: RequestData) -> _ResultT: ...
    def reports(self, data: RequestData) -> _ResultT: ...
