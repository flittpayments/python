# flittpayments Python SDK client


## Payment service provider
A payment service provider (PSP) offers shops online services for accepting electronic payments by a variety of payment methods including credit card, bank-based payments such as direct debit, bank transfer, and real-time bank transfer based on online banking. Typically, they use a software as a service model and form a single payment gateway for their clients (merchants) to multiple payment methods. 
[read more](https://en.wikipedia.org/wiki/Payment_service_provider)

Requirements
------------
- Python (2.4, 2.7, 3.3, 3.4, 3.5, 3.6, 3.7)

Dependencies
------------
- requests
- six

Installation
------------
```bash
pip install flittpayments
```
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

Unlike every other example above, this doesn't use `Api`'s `merchant_id`/`secret_key` at all -
Reports is a separate service (`portal.flitt.com`) with its own `application_id`/`key`
credentials and a short-lived bearer token instead of a per-request signature. `merchant_id`
`1549902` below is a sandbox merchant dedicated to Reports examples with sample data already
attached - it's for this example only, not for actual transactions elsewhere in this README.
For your own reports, use your own `application_id`/`key` (issued separately from your
merchant account) and your own `merchant_id`.

```python
from flittpayments import Api, Payment

api = Api()  # reports() doesn't use Api's merchant_id/secret_key
client = Payment(api=api)
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
report = client.reports(data)
```

Tests
-----------------
First, install `tox` `<http://tox.readthedocs.org/en/latest/>`

To run testing:

```bash
tox
```

This will run all tests, against all supported Python versions.