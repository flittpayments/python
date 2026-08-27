from __future__ import absolute_import, unicode_literals
from flittpayments import Api, exceptions
from flittpayments.api import _mask_sensitive
from flittpayments.configuration import __version__
from .tests_helper import TestCase


class ApiTest(TestCase):
    def setUp(self):
        self.data = self.get_dummy_data()
        self.api = Api(merchant_id=self.data['merchant']['id'],
                       secret_key=self.data['merchant']['secret'])

    def test_request_type(self):
        api = Api(merchant_id=self.data['merchant']['id'],
                  secret_key=self.data['merchant']['secret'],
                  request_type='form')
        self.assertEqual(api.request_type, 'form')

    def test_request_type_xml_not_supported(self):
        with self.assertRaises(ValueError):
            Api(merchant_id=self.data['merchant']['id'],
                secret_key=self.data['merchant']['secret'],
                request_type='xml')

    def test_api_domain(self):
        api = Api(merchant_id=self.data['merchant']['id'],
                  secret_key=self.data['merchant']['secret'],
                  api_domain='api.test.eu')
        self.assertEqual(api.api_url, 'https://api.test.eu/api')

    def test_api_protocol(self):
        api = Api(merchant_id=self.data['merchant']['id'],
                  secret_key=self.data['merchant']['secret'],
                  api_protocol='2.0')
        self.assertEqual(api.api_protocol, '2.0')

    def test_api_except(self):
        with self.assertRaises(ValueError):
            Api(merchant_id=self.data['merchant']['id'],
                secret_key=self.data['merchant']['secret'],
                api_protocol='2.0',
                request_type='form'
                )

    def test_post(self):
        with self.assertRaises(exceptions.ServiceError):
            self.api._request(self.api.api_url,
                              method="POST",
                              data=None,
                              headers=None)

    def test_headers(self):
        self.assertEqual(self.api._headers().get('User-Agent'),
                         'FlittPay-python-sdk/%s' % __version__)
        self.assertEqual(self.api._headers().get('Content-Type'),
                         'application/json; charset=utf-8')

    def test_mask_sensitive_json(self):
        text = '{"card_number": "4444555566661111", "cvv2": "123", "receiver_iban": "GE00TB0000000000000001", "order_id": "123"}'
        masked = _mask_sensitive(text)
        self.assertIn('"card_number": "***"', masked)
        self.assertIn('"cvv2": "***"', masked)
        self.assertIn('"receiver_iban": "***"', masked)
        self.assertIn('"order_id": "123"', masked)

    def test_mask_sensitive_form(self):
        text = 'card_number=4444555566661111&cvv2=123&receiver_iban=GE00TB0000000000000001&order_id=123'
        masked = _mask_sensitive(text)
        self.assertEqual(masked, 'card_number=***&cvv2=***&receiver_iban=***&order_id=123')

    def test_mask_sensitive_falsy_passthrough(self):
        self.assertEqual(_mask_sensitive(''), '')
        self.assertIsNone(_mask_sensitive(None))
