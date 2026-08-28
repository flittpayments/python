from __future__ import print_function

import requests

from flittpayments import Api, Payment
from flittpayments.transport import BaseTransport


class CustomTransport(BaseTransport):
    """Example transport that adds an application-specific header."""

    def __init__(self):
        self.session = requests.Session()

    def request(self, method, url, data=None, headers=None, timeout=None):
        request_headers = dict(headers or {})
        request_headers['X-Application'] = 'custom-sdk-client'
        return self.session.request(
            method,
            url,
            data=data,
            headers=request_headers,
            timeout=timeout,
        )

    def close(self):
        self.session.close()


def main():
    transport = CustomTransport()
    try:
        api = Api(
            merchant_id=123,
            secret_key='secret',
            transport=transport,
        )
        response = Payment(api).recurring({
            'amount': 100,
            'currency': 'GEL',
            'rectoken': 'token-from-an-earlier-payment',
        })
        print(response)
    finally:
        transport.close()


if __name__ == '__main__':
    main()
