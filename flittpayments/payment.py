from __future__ import absolute_import, unicode_literals
from flittpayments.resources import Resource
from datetime import datetime

import flittpayments.helpers as helper
import flittpayments.utils as utils


class Pcidss(Resource):
    def step_one(self, data):
        """
        Accept purchase Pcidss step one
        :param data: order data
        :return: payment result or step two data
        """
        path = '/3dsecure_step1/'
        self.order_id = data.get('order_id') or helper.generate_order_id()
        order_desc = data.get('order_desc') or helper.get_desc(self.order_id)
        params = {
            'order_id': self.order_id,
            'order_desc': order_desc,
            'currency': data.get('currency', ''),
            'amount': data.get('amount', ''),
            'card_number': data.get('card_number', ''),
            'cvv2': data.get('cvv2', ''),
            'expiry_date': data.get('expiry_date', '')
        }
        helper.check_data(params)
        params.update(data)
        result = self.api.post(path, data=params, headers=self.__headers__)
        return self.response(result)

    def step_two(self, data):
        """
        Accept purchase Pcidss step two
        :param data: order data
        :return: payment result
        """
        path = '/3dsecure_step2/'
        params = {
            'order_id': data.get('order_id', ''),
            'pares': data.get('pares', ''),
            'md': data.get('md', '')
        }
        helper.check_data(params)
        params.update(data)
        result = self.api.post(path, data=params, headers=self.__headers__)
        return self.response(result)


class Payment(Resource):
    def p2pcredit(self, data):
        """
        Method P2P card credit
        :param data: order data
        :return: api response
        """
        path = '/p2pcredit/'
        self.order_id = data.get('order_id') or helper.generate_order_id()
        order_desc = data.get('order_desc') or helper.get_desc(self.order_id)
        params = {
            'order_id': self.order_id,
            'order_desc': order_desc,
            'amount': data.get('amount', ''),
            'currency': data.get('currency', '')
        }
        helper.check_data(params)
        params.update(data)
        result = self.api.post(path, data=params, headers=self.__headers__)
        return self.response(result)

    def ibancredit(self, data):
        """
        Method for IBAN credit (withdrawal to IBAN account)
        :param data: payment data
        :return: api response
        """
        path = '/ibancredit/'
        self.order_id = data.get('order_id') or helper.generate_order_id()
        order_desc = data.get('order_desc') or helper.get_desc(self.order_id)
        params = {
            'order_id': self.order_id,
            'order_desc': order_desc,
            'amount': data.get('amount', ''),
            'currency': data.get('currency', ''),
            'receiver_iban': data.get('receiver_iban', '')
        }
        helper.check_data(params)
        params.update(data)
        result = self.api.post(path, data=params, headers=self.__headers__)
        return self.response(result)

    def reports(self, data):
        """
        Method to poll the Reports API (portal.flitt.com) for report data.
        This is a separate service from the rest of this SDK: it
        authenticates with application_id/key - NOT this Payment's Api
        merchant_id/secret_key - via a short-lived bearer token obtained
        from a signed request, not a per-request signature.
        See https://docs.flitt.com/api/reports/
        :param data: report request:
            application_id, key - Reports application credentials
            report_id - report id, required (see docs.flitt.com/api/reports/
                for the available reports)
            filters - optional; list of {'s': field, 'm': operand,
                'v': value}. docs.flitt.com/api/reports/ lists this as
                required, but the live API accepts an empty/omitted list
                just fine (confirmed against report_id 1023 and 745) -
                whether it's meaningful depends on the specific report_id
            merchant_id - optional; a single merchant id. Omit to scope
                the report to every merchant linked to application_id
                instead
            on_page, page - pagination, default 10/1
        :return: {'data': [[...]], 'fields': [...], 'rows_count',
            'rows_on_page', 'rows_page'} on success, or
            {'error': ..., 'err_code': ...}
        """
        application_id = data.get('application_id', '')
        key = data.get('key', '')
        helper.check_data({
            'application_id': application_id,
            'key': key,
            'report_id': data.get('report_id', '')
        })

        date = str(datetime.now())
        token_data = {
            'application_id': application_id,
            'date': date,
            'signature': helper.get_reports_signature(
                key, application_id, date)
        }
        token_result = self.api._request(
            'https://portal.flitt.com/authorizer/token/application/get',
            'POST', data=utils.to_json(token_data),
            headers={'Content-Type': 'application/json'})
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
            'https://portal.flitt.com/api/extend/company/report/',
            'POST', data=utils.to_json(params),
            headers={'Content-Type': 'application/json',
                    'Authorization': 'Token %s' % token})
        return utils.from_json(result)

    def recurring(self, data):
        """
        Method for recurring payment
        :param data: order data
        :return: api response
        """
        path = '/recurring/'
        self.order_id = data.get('order_id') or helper.generate_order_id()
        order_desc = data.get('order_desc') or helper.get_desc(self.order_id)
        params = {
            'order_id': self.order_id,
            'order_desc': order_desc,
            'amount': data.get('amount', ''),
            'currency': data.get('currency', ''),
            'rectoken': data.get('rectoken', '')
        }
        helper.check_data(params)
        params.update(data)
        result = self.api.post(path, data=params, headers=self.__headers__)
        return self.response(result)
