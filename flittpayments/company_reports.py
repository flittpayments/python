from __future__ import absolute_import, unicode_literals

from datetime import datetime

from flittpayments._compat import resolve
from flittpayments.configuration import (__reports_api_url__,
                                         __reports_domain__)
from flittpayments import helpers
from flittpayments import utils


DEFAULT_REPORTS_DOMAIN = __reports_domain__


class CompanyReports(object):
    """Client for the separate Flitt Company Reports service."""

    token_path = '/authorizer/token/application/get'
    report_path = '/api/extend/company/report/'

    def __init__(self, api=None, api_domain=DEFAULT_REPORTS_DOMAIN):
        """
        :param api: Api instance providing the HTTP transport and timeout
        :param api_domain: Reports service domain, portal.flitt.com by default
        """
        self.api = api
        self.api_domain = api_domain
        self.api_url = __reports_api_url__.format(api_domain=api_domain)

    def get(self, data):
        """
        Fetch a company report.

        Reports uses its own application_id/key credentials and does not use
        Api.merchant_id or Api.secret_key. The application credentials are
        exchanged for a short-lived token before requesting the report.

        :param data: report request containing application_id, key, report_id;
            optional filters, merchant_id, on_page and page
        :return: report response dictionary, or an awaitable resolving to it
        """
        application_id = data.get('application_id', '')
        key = data.get('key', '')
        helpers.check_data({
            'application_id': application_id,
            'key': key,
            'report_id': data.get('report_id', '')
        })

        date = str(datetime.now())
        token_data = {
            'application_id': application_id,
            'date': date,
            'signature': helpers.get_reports_signature(
                key, application_id, date)
        }
        token_result = self.api._request(
            utils.join_url(self.api_url, self.token_path),
            'POST', data=utils.to_json(token_data),
            headers={'Content-Type': 'application/json'})
        return resolve(
            token_result,
            lambda result: self._request_report(data, result)
        )

    def reports(self, data):
        """Alias for :meth:`get` for callers migrating from Payment."""
        return self.get(data)

    def _request_report(self, data, token_result):
        token = utils.from_json(token_result).get('token')
        params = {
            'report_id': data.get('report_id'),
            'filters': data.get('filters', []),
            'on_page': data.get('on_page', 10),
            'page': data.get('page', 1)
        }
        if 'merchant_id' in data:
            params['merchant_id'] = data['merchant_id']

        result = self.api._request(
            utils.join_url(self.api_url, self.report_path),
            'POST', data=utils.to_json(params),
            headers={'Content-Type': 'application/json',
                     'Authorization': 'Token %s' % token})
        return resolve(result, utils.from_json)
