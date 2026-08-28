from __future__ import absolute_import, unicode_literals

import json
import os
from datetime import datetime, timedelta
from unittest import TestCase

from flittpayments import Api, CompanyReports, Payment
from flittpayments import helpers
from flittpayments.transport import BaseTransport


class FakeResponse(object):
    def __init__(self, content, status_code=200):
        self.content = content
        self.status_code = status_code


class QueueTransport(BaseTransport):
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def request(self, method, url, data=None, headers=None, timeout=None):
        self.requests.append({
            'method': method,
            'url': url,
            'data': data,
            'headers': headers,
            'timeout': timeout,
        })
        return self.responses.pop(0)


def reports_transport():
    return QueueTransport([
        FakeResponse(b'{"token": "report-token"}'),
        FakeResponse(b'{"fields": [], "rows_count": 0}'),
    ])


class CompanyReportsTest(TestCase):
    def setUp(self):
        self.data = {
            'application_id': 'application',
            'key': 'private-key',
            'report_id': 745,
            'merchant_id': 1549902,
        }

    def test_get_uses_default_domain_and_report_credentials(self):
        transport = reports_transport()
        api = Api(transport=transport)

        response = CompanyReports(api=api).get(self.data)

        self.assertEqual(response['rows_count'], 0)
        token_request, report_request = transport.requests
        self.assertEqual(
            token_request['url'],
            'https://portal.flitt.com/authorizer/token/application/get'
        )
        self.assertEqual(
            report_request['url'],
            'https://portal.flitt.com/api/extend/company/report/'
        )
        token_data = json.loads(token_request['data'])
        self.assertEqual(token_data['application_id'], 'application')
        self.assertEqual(
            token_data['signature'],
            helpers.get_reports_signature(
                'private-key', 'application', token_data['date'])
        )
        report_data = json.loads(report_request['data'])
        self.assertEqual(report_data['report_id'], 745)
        self.assertEqual(report_data['merchant_id'], 1549902)
        self.assertEqual(report_data['filters'], [])
        self.assertNotIn('application_id', report_data)
        self.assertNotIn('key', report_data)
        self.assertEqual(
            report_request['headers']['Authorization'],
            'Token report-token'
        )

    def test_get_accepts_custom_domain(self):
        transport = reports_transport()
        api = Api(transport=transport)

        CompanyReports(
            api=api,
            api_domain='reports.example.test'
        ).get(self.data)

        self.assertEqual(
            transport.requests[0]['url'],
            'https://reports.example.test/authorizer/token/application/get'
        )
        self.assertEqual(
            transport.requests[1]['url'],
            'https://reports.example.test/api/extend/company/report/'
        )

    def test_payment_reports_keeps_backward_compatibility(self):
        transport = reports_transport()
        api = Api(transport=transport)

        response = Payment(api=api).reports(self.data)

        self.assertEqual(response['rows_count'], 0)
        self.assertEqual(
            transport.requests[1]['url'],
            'https://portal.flitt.com/api/extend/company/report/'
        )

    def test_reports_is_an_alias_for_get(self):
        transport = reports_transport()
        api = Api(transport=transport)

        response = CompanyReports(api=api).reports(self.data)

        self.assertEqual(response['rows_count'], 0)


class CompanyReportsIntegrationTest(TestCase):
    def setUp(self):
        data_path = os.path.join(
            os.path.dirname(__file__), 'data', 'test_data.json')
        with open(data_path) as data_file:
            self.data = json.load(data_file)

    def test_reports(self):
        # Merchant 1549902 is dedicated to Reports sandbox examples and has
        # sample report data attached; it is not used for transactions.
        data = {
            'filters': [
                {'s': 'order_timestart_from', 'm': 'from',
                 'v': (datetime.now() - timedelta(days=30)).strftime(
                     '%Y-%m-%d')},
                {'s': 'order_timestart_to', 'm': 'to',
                 'v': datetime.now().strftime('%Y-%m-%d')}
            ]
        }
        data.update(self.data['reports_application'])

        response = CompanyReports(api=Api()).get(data)

        self.assertNotIn('error', response)
        self.assertIn('fields', response)
        self.assertGreaterEqual(response.get('rows_count'), 0)
