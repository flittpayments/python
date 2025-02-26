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
checkout = Checkout(api=api)
data = {
    "currency": "USD",
    "amount": 10000
}
url = checkout.url(data).get('checkout_url')
```

Tests
-----------------
First, install `tox` `<http://tox.readthedocs.org/en/latest/>`

To run testing:

```bash
tox
```

This will run all tests, against all supported Python versions.