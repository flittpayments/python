from __future__ import absolute_import, unicode_literals

import json
from flittpayments import Order
from flittpayments.exceptions import RequestError
from .tests_helper import TestCase


class OrderTest(TestCase):
    def setUp(self):
        self.api = self.get_api()
        self.order = Order(api=self.api)
        self.order_id = self.create_order().get('order_id')

    def test_get_order_status(self):
        data = {
            'order_id': self.order_id
        }
        response = self.order.status(data)
        self.assertEqual(response.get('response_status'), 'success')
        self.assertIn('order_status', response)

    def test_refund(self):
        data = {
            'order_id': self.order_id
        }
        data.update(self.data['order_full_data'])
        response = self.order.reverse(data)
        self.assertEqual(response.get('response_status'), 'success')
        self.assertIn('reverse_status', response)

    def test_capture(self):
        data = {
            'order_id': self.order_id
        }
        data.update(self.data['order_full_data'])
        response = self.order.capture(data)
        self.assertEqual(response.get('response_status'), 'success')
        self.assertEqual(response.get('order_id'), self.order_id)
        self.assertEqual(response.get('capture_status'), 'captured')

    def test_capture_full(self):
        data = {
            'order_id': self.order_id,
            'currency': self.data['order_full_data']['currency']
        }
        response = self.order.capture_full(data)
        self.assertEqual(response.get('response_status'), 'success')
        self.assertEqual(response.get('order_id'), self.order_id)
        self.assertEqual(response.get('capture_status'), 'captured')

    def test_reverse_full(self):
        data = {
            'order_id': self.order_id,
            'currency': self.data['order_full_data']['currency']
        }
        response = self.order.reverse_full(data)
        self.assertEqual(response.get('response_status'), 'success')
        self.assertIn('reverse_status', response)

    def test_settlement(self):
        self.api.api_protocol = '2.0'
        data = {
            'operation_id': self.order_id,
            'receiver': [
                {
                    'requisites': {
                        'amount': 500,
                        'merchant_id': 1549901
                    },
                    'type': 'merchant'
                },
                {
                    'requisites': {
                        'amount': 500,
                        'merchant_id': 1549901
                    },
                    'type': 'merchant'
                }
            ]
        }
        data.update(self.data['order_full_data'])
        data_capture = {
            'order_id': self.order_id
        }
        data_capture.update(self.data['order_full_data'])
        self.order.capture(data_capture)
        response = self.order.settlement(data)
        response_data = json.loads(response.get('data'))
        self.assertEqual(response_data.get('order')['order_status'], 'created')
        self.assertIn('payment_id', response_data.get('order'))

    def test_fiscal_data_missing_order_id(self):
        # Fiscalisation is Uzbekistan-only and this sandbox merchant isn't
        # configured for it, so a live positive-path response isn't
        # reachable here - but the required-field guard is deterministic.
        with self.assertRaises(RequestError):
            self.order.fiscal_data({})
