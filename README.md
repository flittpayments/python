# flittpayments Python SDK client


## Payment service provider
A payment service provider (PSP) offers shops online services for accepting electronic payments by a variety of payment methods including credit card, bank-based payments such as direct debit, bank transfer, and real-time bank transfer based on online banking. Typically, they use a software as a service model and form a single payment gateway for their clients (merchants) to multiple payment methods. 
[read more](https://en.wikipedia.org/wiki/Payment_service_provider)

Requirements
------------
- Python 3.5+

Dependencies
------------
- requests

Installation
------------
```bash
pip install flittpayments
```

For asynchronous requests on Python 3.10 or newer, install the `httpx2`
transport extra:

```bash
pip install "flittpayments[async]"
```

The synchronous API remains the default and supports Python 3.5+.
`AsyncTransport` requires Python 3.10+ because `httpx2` does not support
older Python versions.

### Simple start

```python
from flittpayments import Api, Checkout
api = Api(merchant_id=1549901,
          secret_key='test')
client = Checkout(api=api)
data = {
    "currency": "GEL",
    "amount": 10000
}
url = client.url(data).get('checkout_url')
```

### Asynchronous transport

Every SDK resource method becomes awaitable when its `Api` uses
`AsyncTransport`; method names and request/response data stay the same.
The package includes PEP 561 type information, so PyCharm and other type
checkers infer an awaitable result for `AsyncTransport` and a regular `dict`
for the default `SyncTransport`.

```python
import asyncio

from flittpayments import Api, Payment
from flittpayments.transport import AsyncTransport


async def main():
    async with AsyncTransport() as transport:
        api = Api(
            merchant_id=123,
            secret_key="secret",
            transport=transport,
        )
        payment = Payment(api)
        response = await payment.recurring({
            "amount": 100,
            "currency": "GEL",
            "rectoken": "token-from-an-earlier-payment",
        })
        print(response)


asyncio.run(main())
```

A single resource instance is safe to reuse across concurrent tasks. Its
`order_id` and response-backed attributes are task-local, so one request
cannot overwrite another request's state:

```python
responses = await asyncio.gather(
    payment.recurring(first_payment),
    payment.recurring(second_payment),
    payment.recurring(third_payment),
)
```

Use the returned values in the parent task. Task-local attributes such as
`payment.order_id` remain available inside the task that awaited the request
and do not leak from child tasks after `gather()` completes.

`SyncTransport` uses `requests` and is created automatically when
`transport` is omitted. It can also be managed explicitly:

```python
from flittpayments import Api, Payment
from flittpayments.transport import SyncTransport

with SyncTransport() as transport:
    api = Api(merchant_id=123, secret_key="secret", transport=transport)
    response = Payment(api).recurring(data)
```

### Custom transport

Custom transports inherit from `BaseTransport` and implement `request`. The
method may return a response directly or an awaitable. The response object
must expose `status_code` and `content` attributes.

```python
import requests

from flittpayments.transport import BaseTransport


class CustomTransport(BaseTransport):
    def __init__(self):
        self.session = requests.Session()

    def request(self, method, url, data=None, headers=None, timeout=None):
        return self.session.request(
            method,
            url,
            data=data,
            headers=headers,
            timeout=timeout,
        )
```

Complete runnable examples are available in `examples/async_recurring.py` and
`examples/custom_transport.py`.

### Get order status

```python
from flittpayments import Order
order_id = client.order_id  # order_id from checkout.url()/payment.p2pcredit()/etc.
client = Order(api=api)
status = client.status({"order_id": order_id}).get('order_status')
```

### IBAN withdrawal

IBAN withdrawal is a payout, not a purchase — sign it with your **payout** secret key
(`testcredit` in the sandbox), not the purchase one used everywhere else in this README.

```python
from flittpayments import Api, Payment
api = Api(merchant_id=1549901,
          secret_key='testcredit')
client = Payment(api=api)
data = {
    "currency": "GEL",
    "amount": 10000,
    "receiver_iban": "GE00TB0000000000000001"
}
response = client.ibancredit(data)
```

### P2P credit

Sends money to a card using a `rectoken` obtained from an earlier purchase - the card number
itself is never collected again. Same payout-vs-purchase rule as IBAN withdrawal above: the
purchase is signed with the purchase secret key, the credit with the **payout** one.

```python
from flittpayments import Api, Pcidss, Payment

# a purchase that asks for a reusable token
api = Api(merchant_id=1549901,
          secret_key='test')
client = Pcidss(api=api)
data = {
    "currency": "GEL",
    "amount": 100,
    "card_number": "4444555511116666",
    "cvv2": "123",
    "expiry_date": "1224",
    "required_rectoken": "Y"
}
rectoken = client.step_one(data).get('rectoken')

# later, send funds to that same card without ever touching the card number again
api = Api(merchant_id=1549901,
          secret_key='testcredit')
client = Payment(api=api)
data = {
    "currency": "GEL",
    "amount": 10000,
    "receiver_rectoken": rectoken
}
response = client.p2pcredit(data)
```

### Open Banking (OPB)

```python
from flittpayments import Api, Checkout
api = Api(merchant_id=1549901,
          secret_key='test')
client = Checkout(api=api)
data = {
    "currency": "GEL",
    "amount": 10000,
    "payment_method": "tbc"  # tbc, bog, liberty, credo, x (demo)
}
url = client.open_banking(data).get('checkout_url')
```

**Important:** `checkout_url` here is a bank-app deeplink/SCA url, not a hosted Flitt page. Hand it
unmodified to the customer's device as the direct result of an explicit user action (an OS-level url
intent on mobile, or a QR code on desktop). Never auto-redirect to it, rewrite/append to it, or load
it in an iframe/hidden webview, and never allowlist-validate the bank host yourself. Confirm payment
only via the Flitt server callback or `Order.status`, never from the client return.

### Installments

```python
from flittpayments import Api, Checkout
api = Api(merchant_id=1549901,
          secret_key='test')
client = Checkout(api=api)
data = {
    "currency": "GEL",
    "amount": 5000,  # minimum order amount is 50 GEL
    "payment_method": "tbc"  # currently tbc or x (demo) only
}
url = client.installments(data).get('checkout_url')
```

Same `checkout_url` handling rules as Open Banking above apply.

### Reports

Company Reports is a separate service with its own `application_id`/`key`
credentials and a short-lived bearer token. It does not use `Api`'s
`merchant_id` or `secret_key`. The default service domain is
`portal.flitt.com`; pass `api_domain` to `CompanyReports` to override it.

Merchant `1549902` below is dedicated to sandbox Reports examples and has
sample data attached. For your own reports, use your own Reports credentials
and merchant id.

```python
from flittpayments import Api, CompanyReports

api = Api()  # supplies the transport and timeout only
reports = CompanyReports(api=api)
data = {
    "application_id": "1019",
    "key": "test",
    "report_id": 745,
    "merchant_id": 1549902,
    "filters": [
        {"s": "order_timestart_from", "m": "from", "v": "2026-08-01"},
        {"s": "order_timestart_to", "m": "to", "v": "2026-08-27"}
    ]
}
report = reports.get(data)
```

For a custom Reports deployment:

```python
reports = CompanyReports(api=api, api_domain="reports.example.com")
```

`Payment(api).reports(data)` remains available as a backward-compatible
shortcut and uses the default Reports domain. New code should use
`CompanyReports` directly.

Tests
-----------------
First, install `tox` `<https://tox.readthedocs.io/en/latest/>`

To run testing:

```bash
tox
```

This will run all tests, against all supported Python versions.
