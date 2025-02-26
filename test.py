from flittpayments import Api, Checkout

api = Api(merchant_id=1549901,
          secret_key='test',
          request_type='json',
          api_protocol='1.0',
          api_domain='pay.flitt.com')  # json - is default
checkout = Checkout(api=api)
data = {
    "preauth": 'Y',
    "currency": "GEL",
    "amount": 10000,
    "reservation_data": {
        'test': 1,
        'test2': 2
    }
}
response = checkout.url(data)
