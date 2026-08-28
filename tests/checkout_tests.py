from __future__ import absolute_import, unicode_literals
from flittpayments import Checkout, Order
from .tests_helper import TestCase

import json
import uuid


class CheckoutTest(TestCase):
    def setUp(self):
        self.api = self.get_api()
        self.checkout = Checkout(api=self.api)

    def test_create_url_json(self):
        response = self.checkout.url(self.data.get('checkout_data'))
        self.assertEqual(response.get('response_status'), 'success')
        self.assertEqual(self.api._headers().get('Content-Type'),
                         'application/json; charset=utf-8')
        self.assertIn('checkout_url', response)
        self.assertEqual(len(response.get('checkout_url')) > 0, True)

    def test_get_order_id(self):
        data = {
            'order_id': str(uuid.uuid4())
        }
        data.update(self.data.get('checkout_data'))
        self.checkout.url(data)
        self.assertEqual(self.checkout.order_id, data.get('order_id'))

    def test_get_order_status_after_checkout_url(self):
        # Mirrors the README's "Get order status" example: check the status
        # of an order_id obtained from checkout.url(), not a fresh Pcidss
        # order like order_tests.py's own test_get_order_status does.
        self.checkout.url(self.data.get('checkout_data'))
        order = Order(api=self.api)
        status = order.status({'order_id': self.checkout.order_id})
        self.assertEqual(status.get('response_status'), 'success')
        self.assertEqual(status.get('order_status'), 'created')

    def test_create_url_json_v2(self):
        self.api.api_protocol = '2.0'
        response = self.checkout.url(self.data.get('checkout_data'))
        self.assertEqual(self.api._headers().get('Content-Type'),
                         'application/json; charset=utf-8')
        self.assertEqual(response.get('version'), '2.0')
        self.assertEqual(len(response.get('data')) > 0, True)

    def test_create_subscb_json_v2(self):
        self.api.api_protocol = '2.0'
        data = self.data.get('checkout_data')
        recurring_data = {
            'recurring_data': {
                'start_time': '2028-11-11',
                'amount': '234324',
                'every': '40',
                'period': 'day'
            }
        }
        data.update(recurring_data)
        response = self.checkout.url(data)
        self.assertEqual(self.api._headers().get('Content-Type'),
                         'application/json; charset=utf-8')
        self.assertEqual(response.get('version'), '2.0')
        self.assertEqual(len(response.get('data')) > 0, True)

    def test_subscription(self):
        self.api.api_protocol = '2.0'
        data = self.data.get('checkout_data').copy()
        data.update({
            'recurring_data': {
                'start_time': '2028-11-11',
                'amount': 10000,
                'every': 1,
                'period': 'month',
                'readonly': 'y',
                'state': 'y'
            }
        })
        response = self.checkout.subscription(data)
        response_data = json.loads(response.get('data'))
        self.assertIn('checkout_url', response_data.get('order'))
        self.assertIn('payment_id', response_data.get('order'))

    def test_subscription_invalid_period(self):
        self.api.api_protocol = '2.0'
        data = self.data.get('checkout_data').copy()
        data.update({
            'recurring_data': {
                'start_time': '2028-11-11',
                'amount': 10000,
                'every': 1,
                'period': 'year',
                'readonly': 'y',
                'state': 'y'
            }
        })
        self.assertRaises(ValueError, self.checkout.subscription, data)

    def test_subscription_stop_requires_v2(self):
        # A genuine "stop" needs a subscription order a customer has actually
        # completed via the checkout_url redirect - not reachable from a
        # server-side-only test. The v2.0-only guard is, though.
        self.api.api_protocol = '1.0'
        self.assertRaises(Exception, self.checkout.subscription_stop, 'whatever')

    def test_create_url_form(self):
        self.api.request_type = 'form'
        response = self.checkout.url(self.data.get('checkout_data'))

        self.assertEqual(response.get('response_status'), 'success')
        self.assertEqual(self.api._headers().get('Content-Type'),
                         'application/x-www-form-urlencoded; charset=utf-8')
        self.assertIn('checkout_url', response)
        self.assertEqual(len(response.get('checkout_url')) > 0, True)

    def test_create_token(self):
        response = self.checkout.token(self.data.get('checkout_data'))
        self.assertEqual(response.get('response_status'), 'success')
        self.assertEqual(self.api._headers().get('Content-Type'),
                         'application/json; charset=utf-8')
        self.assertIn('token', response)
        self.assertEqual(len(response.get('token')) > 0, True)

    def test_create_url_verify(self):
        response = self.checkout.verification(self.data.get('checkout_data'))
        self.assertEqual(response.get('response_status'), 'success')
        self.assertEqual(self.api._headers().get('Content-Type'),
                         'application/json; charset=utf-8')
        self.assertIn('checkout_url', response)
        self.assertEqual(len(response.get('checkout_url')) > 0, True)

    def test_open_banking(self):
        data = self.data.get('checkout_data').copy()
        data.update(self.data.get('open_banking_data'))
        response = self.checkout.open_banking(data)
        self.assertEqual(response.get('response_status'), 'success')
        self.assertIn('checkout_url', response)
        self.assertEqual(len(response.get('checkout_url')) > 0, True)

    def test_open_banking_invalid_payment_method(self):
        data = self.data.get('checkout_data').copy()
        data.update({'payment_method': 'invalid'})
        self.assertRaises(ValueError, self.checkout.open_banking, data)

    def test_installments(self):
        data = self.data.get('checkout_data').copy()
        data.update(self.data.get('installments_data'))
        response = self.checkout.installments(data)
        self.assertEqual(response.get('response_status'), 'success')
        self.assertIn('checkout_url', response)
        self.assertEqual(len(response.get('checkout_url')) > 0, True)

    def test_installments_invalid_payment_method(self):
        data = self.data.get('checkout_data').copy()
        data.update({'payment_method': 'bog'})
        self.assertRaises(ValueError, self.checkout.installments, data)
