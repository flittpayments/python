from typing import Any, Dict

from flittpayments import Api, Checkout


api = Api(merchant_id=123, secret_key='secret')
payment = Checkout(api)
response: Dict[str, Any] = payment.url({
    'amount': 100,
    'currency': 'GEL',
})
