import asyncio

from flittpayments import Api, Payment
from flittpayments.transport import AsyncTransport


async def main():
    data = {
        'amount': 100,
        'currency': 'GEL',
        'rectoken': 'token-from-an-earlier-payment',
    }

    async with AsyncTransport() as transport:
        api = Api(
            merchant_id=123,
            secret_key='secret',
            transport=transport,
        )
        response = await Payment(api).recurring(data)
        print(response)


if __name__ == '__main__':
    asyncio.run(main())
