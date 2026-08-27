from __future__ import absolute_import, unicode_literals
from flittpayments.resources import Resource

import flittpayments.utils as utils
import flittpayments.helpers as helper


class Order(Resource):
    def settlement(self, data):
        """
        Method for create split order
        :param data: split order data
        :return: api response
        """
        if self.api.api_protocol != '2.0':
            raise Exception('This method allowed only for v2.0')
        path = '/settlement/'
        params = {
            'order_type': data.get('order_type', 'settlement'),
            'order_id': data.get('order_id') or helper.generate_order_id(),
            'operation_id': data.get('operation_id', ''),
            'receiver': data.get('receiver', [])
        }
        helper.check_data(params)
        params.update(data)
        result = self.api.post(path, data=params, headers=self.__headers__)

        return self.response(result)

    def capture(self, data):
        """
        Method for capturing order
        :param data: capture order data
        :return: api response
        """
        path = '/capture/order_id/'
        params = {
            'order_id': data.get('order_id', ''),
            'amount': data.get('amount', ''),
            'currency': data.get('currency', '')
        }
        helper.check_data(params)
        params.update(data)
        result = self.api.post(path, data=params, headers=self.__headers__)
        return self.response(result)

    def capture_full(self, data):
        """
        Method for capturing the full amount currently available on the order,
        net of the client fee already charged.

        Order status is fetched first, then:
            amount = actual_amount - additional_info.client_fee
        :param data: capture order data (order_id, currency, ...); 'amount' is
            derived from order status and does not need to be provided
        :return: api response
        """
        status = self.status({'order_id': data.get('order_id', '')})
        additional_info = self._additional_info(status)
        actual_amount = int(status.get('actual_amount') or 0)
        client_fee = int(additional_info.get('client_fee') or 0)

        params = dict(data)
        params['amount'] = actual_amount - client_fee
        return self.capture(params)

    def reverse(self, data):
        """
        Method to reverse order
        :param data: reverse order data
        :return: api response
        """
        path = '/reverse/order_id/'
        params = {
            'order_id': data.get('order_id', ''),
            'amount': data.get('amount', ''),
            'currency': data.get('currency', '')
        }
        helper.check_data(params)
        params.update(data)
        result = self.api.post(path, data=params, headers=self.__headers__)
        return self.response(result)

    def reverse_full(self, data):
        """
        Method for reversing the full amount currently available on the order,
        net of the client fee already charged and any amount already reversed.

        Order status is fetched first, then:
            base = actual_amount if additional_info.capture_amount == 0
                   else additional_info.capture_amount
            amount = base - additional_info.client_fee - reversal_amount
        :param data: reverse order data (order_id, currency, ...); 'amount' is
            derived from order status and does not need to be provided
        :return: api response
        """
        status = self.status({'order_id': data.get('order_id', '')})
        additional_info = self._additional_info(status)
        actual_amount = int(status.get('actual_amount') or 0)
        reversal_amount = int(status.get('reversal_amount') or 0)
        client_fee = int(additional_info.get('client_fee') or 0)
        capture_amount = int(additional_info.get('capture_amount') or 0)
        base_amount = actual_amount if capture_amount == 0 else capture_amount

        params = dict(data)
        params['amount'] = base_amount - client_fee - reversal_amount
        return self.reverse(params)

    @staticmethod
    def _additional_info(status):
        """
        additional_info comes back as a nested object for JSON responses but
        as a JSON-encoded string for XML/form responses; normalize to a dict.
        :param status: parsed Order.status() response
        :return: additional_info dict
        """
        additional_info = status.get('additional_info') or {}
        if isinstance(additional_info, str):
            additional_info = utils.from_json(additional_info)
        return additional_info

    def status(self, data):
        """
        Method for checking order status
        :param data: order data
        :return: api response
        """
        path = '/status/order_id/'
        params = {
            'order_id': data.get('order_id', '')
        }
        helper.check_data(params)
        params.update(data)
        result = self.api.post(path, data=params, headers=self.__headers__)
        return self.response(result)

    def transaction_list(self, data):
        """
        Method for getting order transaction list
        :param data: order data
        :return: api response
        """
        path = '/transaction_list/'
        params = {
            'order_id': data.get('order_id', '')
        }
        helper.check_data(params)
        params.update(data)
        """
        only json allowed all other methods returns 500 error
        """
        self.api.request_type = 'json'
        result = self.api.post(path, data=params, headers=self.__headers__)
        return self.response(result)

    def atol_logs(self, data):
        """
        Method for getting order atol logs
        :param data: order data
        :return: api response
        """
        path = '/get_atol_logs/'
        params = {
            'order_id': data.get('order_id', '')
        }
        helper.check_data(params)
        params.update(data)
        result = self.api.post(path, data=params, headers=self.__headers__)
        return utils.from_json(result).get('response')
