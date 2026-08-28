from __future__ import absolute_import, unicode_literals
from flittpayments.resources import Resource
from flittpayments.company_reports import CompanyReports

import flittpayments.helpers as helper


class Pcidss(Resource):
    def step_one(self, data):
        """
        Accept purchase Pcidss step one
        :param data: order data
        :return: payment result or step two data
        """
        path = '/3dsecure_step1/'
        order_id = data.get('order_id') or helper.generate_order_id()
        order_desc = data.get('order_desc') or helper.get_desc(order_id)
        params = {
            'order_id': order_id,
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
        return self.response(result, order_id=order_id)

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
        order_id = data.get('order_id') or helper.generate_order_id()
        order_desc = data.get('order_desc') or helper.get_desc(order_id)
        params = {
            'order_id': order_id,
            'order_desc': order_desc,
            'amount': data.get('amount', ''),
            'currency': data.get('currency', '')
        }
        helper.check_data(params)
        params.update(data)
        result = self.api.post(path, data=params, headers=self.__headers__)
        return self.response(result, order_id=order_id)

    def ibancredit(self, data):
        """
        Method for IBAN credit (withdrawal to IBAN account)
        :param data: payment data
        :return: api response
        """
        path = '/ibancredit/'
        order_id = data.get('order_id') or helper.generate_order_id()
        order_desc = data.get('order_desc') or helper.get_desc(order_id)
        params = {
            'order_id': order_id,
            'order_desc': order_desc,
            'amount': data.get('amount', ''),
            'currency': data.get('currency', ''),
            'receiver_iban': data.get('receiver_iban', '')
        }
        helper.check_data(params)
        params.update(data)
        result = self.api.post(path, data=params, headers=self.__headers__)
        return self.response(result, order_id=order_id)

    def reports(self, data):
        """
        Compatibility shortcut for CompanyReports(api=self.api).get(data).

        New code should use CompanyReports directly so its separate domain
        and credentials are explicit.
        """
        return CompanyReports(api=self.api).get(data)

    def recurring(self, data):
        """
        Method for recurring payment
        :param data: order data
        :return: api response
        """
        path = '/recurring/'
        order_id = data.get('order_id') or helper.generate_order_id()
        order_desc = data.get('order_desc') or helper.get_desc(order_id)
        params = {
            'order_id': order_id,
            'order_desc': order_desc,
            'amount': data.get('amount', ''),
            'currency': data.get('currency', ''),
            'rectoken': data.get('rectoken', '')
        }
        helper.check_data(params)
        params.update(data)
        result = self.api.post(path, data=params, headers=self.__headers__)
        return self.response(result, order_id=order_id)
