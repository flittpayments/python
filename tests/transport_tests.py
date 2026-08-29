from __future__ import absolute_import, unicode_literals

import json
import asyncio
import sys
import unittest

from flittpayments import (Api, Checkout, CompanyReports, Order, Payment,
                           Pcidss)
from flittpayments._compat import resolve
from flittpayments.exceptions import ServiceError
from flittpayments.transport import (AsyncTransport, BaseTransport,
                                     SyncTransport)


class FakeResponse(object):
    def __init__(self, content, status_code=200):
        self.content = content
        self.status_code = status_code


def json_response(response):
    content = json.dumps({'response': response}).encode('utf-8')
    return FakeResponse(content)


class QueueTransport(BaseTransport):
    def __init__(self, responses, loop=None):
        self.responses = list(responses)
        self.requests = []
        self.loop = loop

    def request(self, method, url, data=None, headers=None, timeout=None):
        self.requests.append({
            'method': method,
            'url': url,
            'data': data,
            'headers': headers,
            'timeout': timeout,
        })
        response = self.responses.pop(0)
        if self.loop is None:
            return response
        future = self.loop.create_future()
        future.set_result(response)
        return future


class DelayedEchoTransport(BaseTransport):
    def __init__(self, loop):
        self.loop = loop

    def request(self, method, url, data=None, headers=None, timeout=None):
        request = json.loads(data)['request']
        order_id = request['order_id']
        response = json_response({
            'response_status': 'success',
            'order_status': 'approved',
            'order_id': order_id,
            'marker': 'response-%s' % order_id,
        })
        future = self.loop.create_future()
        delays = {'a': 0.03, 'b': 0.01, 'c': 0.02}
        self.loop.call_later(delays[order_id], future.set_result, response)
        return future


class IncompleteTransport(BaseTransport):
    pass


class FakeAsyncClient(object):
    def __init__(self, loop, response):
        self.loop = loop
        self.response = response
        self.request_args = None
        self.entered = False
        self.closed = False

    def _future(self, result):
        future = self.loop.create_future()
        future.set_result(result)
        return future

    def request(self, method, url, **kwargs):
        self.request_args = (method, url, kwargs)
        return self._future(self.response)

    def __aenter__(self):
        self.entered = True
        return self._future(self)

    def __aexit__(self, exc_type, exc_value, traceback):
        self.closed = True
        return self._future(False)

    def aclose(self):
        self.closed = True
        return self._future(None)


class TransportTest(unittest.TestCase):
    def setUp(self):
        self.loop = None
        if asyncio is not None and sys.version_info >= (3, 5):
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

    def tearDown(self):
        if self.loop is not None:
            self.loop.close()
            asyncio.set_event_loop(None)

    def test_default_transport_is_sync(self):
        api = Api(merchant_id=1, secret_key='secret')
        try:
            self.assertIsInstance(api.transport, SyncTransport)
        finally:
            api.close()

    def test_default_transport_preserves_requests_request_hook(self):
        import flittpayments.api as api_module

        calls = []
        original_request = api_module.requests.request

        def fake_request(method, url, data=None, headers=None, timeout=None):
            calls.append((method, url, timeout))
            return json_response({
                'response_status': 'success',
                'order_status': 'approved',
            })

        api_module.requests.request = fake_request
        try:
            api = Api(merchant_id=1, secret_key='secret')
            response = Payment(api).recurring({
                'amount': 100,
                'currency': 'GEL',
                'rectoken': 'token',
            })
        finally:
            api_module.requests.request = original_request

        self.assertEqual(response['order_status'], 'approved')
        self.assertEqual(calls[0][0], 'POST')
        self.assertEqual(calls[0][2], 30)

    def test_transport_must_inherit_base_transport(self):
        with self.assertRaises(TypeError):
            Api(merchant_id=1, secret_key='secret', transport=object())

    def test_base_transport_is_abstract(self):
        with self.assertRaises(TypeError):
            IncompleteTransport()

    def test_custom_sync_transport_preserves_sync_api(self):
        transport = QueueTransport([
            json_response({
                'response_status': 'success',
                'order_status': 'approved',
                'order_id': 'sync-order',
            })
        ])
        api = Api(merchant_id=1, secret_key='secret', transport=transport)
        payment = Payment(api)
        response = payment.recurring({
            'order_id': 'sync-order',
            'amount': 100,
            'currency': 'GEL',
            'rectoken': 'token',
        })

        self.assertEqual(response['order_status'], 'approved')
        self.assertEqual(payment.order_id, 'sync-order')
        self.assertEqual(payment.order_status, 'approved')
        self.assertEqual(payment.__data__, response)
        self.assertEqual(transport.requests[0]['method'], 'POST')
        self.assertEqual(transport.requests[0]['timeout'], 30)

    @unittest.skipIf(sys.version_info < (3, 5),
                     'native await syntax requires Python 3.5+')
    def test_custom_async_transport_makes_resource_methods_awaitable(self):
        transport = QueueTransport([
            json_response({
                'response_status': 'success',
                'order_status': 'approved',
            })
        ], loop=self.loop)
        api = Api(merchant_id=1, secret_key='secret', transport=transport)
        result = Payment(api).recurring({
            'amount': 100,
            'currency': 'GEL',
            'rectoken': 'token',
        })

        response = self.loop.run_until_complete(result)
        self.assertEqual(response['order_status'], 'approved')

    @unittest.skipIf(sys.version_info < (3, 5),
                     'native await syntax requires Python 3.5+')
    def test_async_resource_result_can_be_scheduled_as_a_task(self):
        transport = QueueTransport([
            json_response({
                'response_status': 'success',
                'order_status': 'approved',
            })
        ], loop=self.loop)
        api = Api(merchant_id=1, secret_key='secret', transport=transport)

        task = self.loop.create_task(Payment(api).recurring({
            'amount': 100,
            'currency': 'GEL',
            'rectoken': 'token',
        }))
        response = self.loop.run_until_complete(task)

        self.assertEqual(response['order_status'], 'approved')

    @unittest.skipIf(sys.version_info < (3, 5),
                     'native await syntax requires Python 3.5+')
    def test_resource_state_is_isolated_between_concurrent_tasks(self):
        transport = DelayedEchoTransport(self.loop)
        api = Api(merchant_id=1, secret_key='secret', transport=transport)
        payment = Payment(api)
        items = [
            {
                'order_id': order_id,
                'amount': 100,
                'currency': 'GEL',
                'rectoken': 'token',
            }
            for order_id in ('a', 'b', 'c')
        ]

        calls = [
            resolve(
                payment.recurring(item),
                lambda response: (
                    response, payment.order_id, payment.marker)
            )
            for item in items
        ]
        results = self.loop.run_until_complete(asyncio.gather(*calls))

        for expected_order_id, result in zip(('a', 'b', 'c'), results):
            response, task_order_id, task_marker = result
            self.assertEqual(response['order_id'], expected_order_id)
            self.assertEqual(task_order_id, expected_order_id)
            self.assertEqual(task_marker, 'response-%s' % expected_order_id)
        self.assertIsNone(payment.order_id)
        self.assertNotIn('marker', payment)

    @unittest.skipIf(sys.version_info < (3, 5),
                     'native await syntax requires Python 3.5+')
    def test_async_checkout_composed_method_is_awaitable(self):
        transport = QueueTransport([
            json_response({
                'response_status': 'success',
                'checkout_url': 'bank-app://checkout',
            })
        ], loop=self.loop)
        api = Api(merchant_id=1, secret_key='secret', transport=transport)

        result = Checkout(api).open_banking({
            'amount': 100,
            'currency': 'GEL',
            'payment_method': 'tbc',
        })
        response = self.loop.run_until_complete(result)

        self.assertEqual(response['checkout_url'], 'bank-app://checkout')

    @unittest.skipIf(sys.version_info < (3, 5),
                     'native await syntax requires Python 3.5+')
    def test_async_pcidss_method_is_awaitable(self):
        transport = QueueTransport([
            json_response({
                'response_status': 'success',
                'order_status': 'approved',
            })
        ], loop=self.loop)
        api = Api(merchant_id=1, secret_key='secret', transport=transport)

        result = Pcidss(api).step_one({
            'amount': 100,
            'currency': 'GEL',
            'card_number': '4444555511116666',
            'cvv2': '123',
            'expiry_date': '1228',
        })
        response = self.loop.run_until_complete(result)

        self.assertEqual(response['order_status'], 'approved')

    @unittest.skipIf(sys.version_info < (3, 5),
                     'native await syntax requires Python 3.5+')
    def test_async_capture_full_awaits_status_before_capture(self):
        transport = QueueTransport([
            json_response({
                'response_status': 'success',
                'actual_amount': '100',
                'additional_info': {'client_fee': '5'},
            }),
            json_response({
                'response_status': 'success',
                'capture_status': 'captured',
            }),
        ], loop=self.loop)
        api = Api(merchant_id=1, secret_key='secret', transport=transport)

        result = Order(api).capture_full({
            'order_id': 'order-1',
            'currency': 'GEL',
        })
        response = self.loop.run_until_complete(result)

        self.assertEqual(response['capture_status'], 'captured')
        self.assertIn('"amount": 95', transport.requests[1]['data'])

    @unittest.skipIf(sys.version_info < (3, 5),
                     'native await syntax requires Python 3.5+')
    def test_async_reverse_full_awaits_status_before_reverse(self):
        transport = QueueTransport([
            json_response({
                'response_status': 'success',
                'actual_amount': '100',
                'reversal_amount': '10',
                'additional_info': {
                    'client_fee': '5',
                    'capture_amount': '80',
                },
            }),
            json_response({
                'response_status': 'success',
                'reverse_status': 'approved',
            }),
        ], loop=self.loop)
        api = Api(merchant_id=1, secret_key='secret', transport=transport)

        result = Order(api).reverse_full({
            'order_id': 'order-1',
            'currency': 'GEL',
        })
        response = self.loop.run_until_complete(result)

        self.assertEqual(response['reverse_status'], 'approved')
        self.assertIn('"amount": 65', transport.requests[1]['data'])

    @unittest.skipIf(sys.version_info < (3, 5),
                     'native await syntax requires Python 3.5+')
    def test_async_transport_errors_are_raised_when_awaited(self):
        transport = QueueTransport([
            FakeResponse(b'failure', status_code=500),
        ], loop=self.loop)
        api = Api(merchant_id=1, secret_key='secret', transport=transport)

        result = Payment(api).recurring({
            'amount': 100,
            'currency': 'GEL',
            'rectoken': 'token',
        })

        with self.assertRaises(ServiceError):
            self.loop.run_until_complete(result)

    @unittest.skipIf(sys.version_info < (3, 5),
                     'native await syntax requires Python 3.5+')
    def test_async_reports_awaits_token_before_report(self):
        transport = QueueTransport([
            FakeResponse(b'{"token": "report-token"}'),
            FakeResponse(b'{"fields": [], "rows_count": 0}'),
        ], loop=self.loop)
        api = Api(transport=transport)

        result = CompanyReports(api).get({
            'application_id': 'application',
            'key': 'key',
            'report_id': 1,
        })
        response = self.loop.run_until_complete(result)

        self.assertEqual(response['rows_count'], 0)
        self.assertEqual(
            transport.requests[1]['headers']['Authorization'],
            'Token report-token'
        )

    @unittest.skipIf(sys.version_info < (3, 10),
                     'httpx2 requires Python 3.10+')
    def test_async_transport_wraps_async_client(self):
        fake_client = FakeAsyncClient(
            self.loop,
            FakeResponse(b'{"response": {"response_status": "success"}}')
        )
        transport = AsyncTransport(client=fake_client)

        entered = self.loop.run_until_complete(transport.__aenter__())
        response = self.loop.run_until_complete(transport.request(
            'POST',
            'https://example.test/',
            data='payload',
            headers={'Content-Type': 'application/json'},
            timeout=15,
        ))
        self.loop.run_until_complete(transport.__aexit__(None, None, None))

        self.assertIs(entered, transport)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(fake_client.request_args[2]['content'], 'payload')
        self.assertEqual(fake_client.request_args[2]['timeout'], 15)
        self.assertTrue(fake_client.entered)
        self.assertTrue(fake_client.closed)


if __name__ == '__main__':
    unittest.main()
