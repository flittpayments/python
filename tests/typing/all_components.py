from typing import Any, Awaitable, Dict, Mapping, Optional, Union

from flittpayments import (Api, Checkout, CompanyReports, Order, Payment,
                           Pcidss)
from flittpayments.transport import AsyncTransport, BaseTransport


Response = Dict[str, Any]


class CustomAsyncTransport(BaseTransport[Awaitable[Response]]):
    def request(
        self,
        method: str,
        url: str,
        data: Optional[str] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[Union[int, float]] = None,
    ) -> Awaitable[Any]:
        raise NotImplementedError


async def check_all() -> None:
    transport = AsyncTransport()
    api = Api(merchant_id=1, secret_key='secret', transport=transport)
    checkout = Checkout(api)
    pcidss = Pcidss(api)
    payment = Payment(api)
    order = Order(api)
    reports = CompanyReports(api)

    checkout_response: Response = await checkout.url({})
    pcidss_response: Response = await pcidss.step_one({})
    payment_response: Response = await payment.recurring({})
    order_response: Response = await order.status({})
    reports_response: Response = await reports.get({})

    custom_api = Api(transport=CustomAsyncTransport())
    custom_response: Response = await Payment(custom_api).recurring({})

    print(checkout_response, pcidss_response, payment_response,
          order_response, reports_response, custom_response)
