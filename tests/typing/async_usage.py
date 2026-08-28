from typing import Any, Dict

from flittpayments import Api, Checkout
from flittpayments.transport import AsyncTransport


async def main() -> None:
    async with AsyncTransport() as transport:
        api = Api(
            merchant_id=123,
            secret_key='secret',
            transport=transport,
        )
        payment = Checkout(api)
        response: Dict[str, Any] = await payment.url({
            'amount': 100,
            'currency': 'GEL',
        })
        print(response)
