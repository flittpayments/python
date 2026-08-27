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
- defusedxml

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
checkout = Checkout(api=api)
data = {
    "currency": "USD",
    "amount": 10000
}
url = checkout.url(data).get('checkout_url')
```

### IBAN withdrawal

```python
from flittpayments import Api, Payment
api = Api(merchant_id=1549901,
          secret_key='test')
payment = Payment(api=api)
data = {
    "currency": "GEL",
    "amount": 10000,
    "receiver_iban": "GE00TB0000000000000001"
}
response = payment.ibancredit(data)
```

### Open Banking (OPB)

```python
from flittpayments import Api, Checkout
api = Api(merchant_id=1549901,
          secret_key='test')
checkout = Checkout(api=api)
data = {
    "currency": "GEL",
    "amount": 10000,
    "payment_method": "tbc"  # tbc, bog, liberty, credo, x (demo)
}
url = checkout.open_banking(data).get('checkout_url')
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
checkout = Checkout(api=api)
data = {
    "currency": "GEL",
    "amount": 5000,  # minimum order amount is 50 GEL
    "payment_method": "tbc"  # currently tbc or x (demo) only
}
url = checkout.installments(data).get('checkout_url')
```

Same `checkout_url` handling rules as Open Banking above apply.

Tests
-----------------
First, install `tox` `<http://tox.readthedocs.org/en/latest/>`

To run testing:

```bash
tox
```

This will run all tests, against all supported Python versions.