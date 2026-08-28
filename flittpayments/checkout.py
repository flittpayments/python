from __future__ import absolute_import, unicode_literals
from flittpayments.resources import Resource
from datetime import datetime

import flittpayments.helpers as helper


class Checkout(Resource):
    def url(self, data):
        """
        Method to generate checkout url
        :param data: order data
        :return: api response
        """
        path = '/checkout/url/'
        params = self._required(data)
        result = self.api.post(path, data=params, headers=self.__headers__)

        return self.response(result, order_id=params['order_id'])

    def token(self, data):
        """
        Method to generate checkout token
        :param data: order data
        :return: api response
        """
        path = '/checkout/token/'
        params = self._required(data)
        result = self.api.post(path, data=params, headers=self.__headers__)

        return self.response(result, order_id=params['order_id'])

    def verification(self, data):
        """
        Method to generate checkout verification url
        :param data: order data
        :return: api response
        """
        path = '/checkout/url/'
        verification_data = {
            'verification': 'Y',
            'verification_type': data.get('verification_type', 'code')
        }
        data.update(verification_data)
        params = self._required(data)
        result = self.api.post(path, data=params, headers=self.__headers__)

        return self.response(result, order_id=params['order_id'])

    def subscription(self, data):
        """
        Method to generate checkout url with calendar
        :param data: order data
        data = {
            "currency": "UAH", -> currency ('UAH', 'GEL', 'USD')
            "amount": 10000, -> amount of the order (int)
            "recurring_data": {
                "every": 1, -> frequency of the recurring order (int)
                "amount": 10000, -> amount of the recurring order (int)
                "period": 'month', -> period of the recurring order
                    ('day', 'week', 'month')
                "start_time": '2020-07-24', -> start date
                    ('YYYY-MM-DD')
                "readonly": 'y', -> can the user change recurring params
                    ('y', 'n')
                "state": 'y' -> default state after opening the order url
                    ('y', 'n')
            }
        }
        :return: api response
        """
        if self.api.api_protocol != '2.0':
            raise Exception('This method allowed only for v2.0')
        path = '/checkout/url/'
        recurring_data = data.get('recurring_data', '')
        subscription_data = {
            'subscription': 'Y',
            'recurring_data': {
                'start_time': recurring_data.get('start_time', ''),
                'amount': recurring_data.get('amount', ''),
                'every': recurring_data.get('every', ''),
                'period': recurring_data.get('period', ''),
                'readonly': recurring_data.get('readonly', ''),
                'state': recurring_data.get('state', '')
            }
        }

        helper.check_data(subscription_data['recurring_data'])
        self._validate_recurring_data(subscription_data['recurring_data'])
        subscription_data.update(data)
        params = self._required(subscription_data)
        result = self.api.post(path, data=params, headers=self.__headers__)

        return self.response(result, order_id=params['order_id'])

    def subscription_stop(self, order_id):
        """
          Stop calendar payments
        """
        if self.api.api_protocol != '2.0':
            raise Exception('This method allowed only for v2.0')
        path = '/subscription/'
        params = {'order_id': order_id, 'action': 'stop'}
        result = self.api.post(path, data=params, headers=self.__headers__)

        return self.response(result)

    def open_banking(self, data):
        """
        Method to generate checkout url for Open Banking (OPB) payment
        :param data: order data
        data = {
            "currency": "GEL",
            "amount": 10000,
            "payment_method": "tbc" -> 'tbc','bog','liberty','credo','x'
        }
        :return: api response

        IMPORTANT: the returned `checkout_url` is a bank-app deeplink /
        SCA url, not a hosted Flitt page. Pass it UNMODIFIED to the
        customer's device as the direct result of an explicit user tap
        (an OS-level url intent on mobile, or a QR code on desktop).
        Never auto-redirect to it, never rewrite or append parameters
        to it, never open it in an iframe or hidden webview, and never
        allowlist-validate the bank host yourself. Confirm payment via
        the Flitt server callback or Order.status - never from the
        client-side return alone.
        """
        payment_method = data.get('payment_method', 'x')
        self._validate_payment_method(
            payment_method, ('tbc', 'bog', 'liberty', 'credo', 'x'))
        opb_data = {
            'payment_systems': 'opb',
            'payment_method': payment_method
        }
        opb_data.update(data)

        return self.url(opb_data)

    def installments(self, data):
        """
        Method to generate checkout url for Installments payment
        :param data: order data
        data = {
            "currency": "GEL",
            "amount": 5000, -> minimum order amount is 50 GEL
            "payment_method": "tbc" -> 'tbc' or 'x' (TBC-only rollout)
        }
        :return: api response

        See open_banking() docstring for checkout_url handling rules -
        the same restrictions apply here.
        """
        payment_method = data.get('payment_method', 'x')
        self._validate_payment_method(payment_method, ('tbc', 'x'))
        installments_data = {
            'payment_systems': 'installments',
            'payment_method': payment_method
        }
        installments_data.update(data)

        return self.url(installments_data)

    @staticmethod
    def _validate_payment_method(payment_method, allowed):
        """
        Validation payment_method against allowed values
        :param payment_method: payment method to validate
        :param allowed: tuple of allowed values
        :return: exception
        """
        if payment_method not in allowed:
            raise ValueError(
                "Incorrect payment_method. %s is allowed" % (allowed,))

    @staticmethod
    def _validate_recurring_data(data):
        """
        Validation recurring data params
        :param data: recurring data
        :return: exception
        """
        try:
            datetime.strptime(data['start_time'], '%Y-%m-%d')
        except ValueError:
            raise ValueError(
                "Incorrect date format. 'Y-m-d' is allowed")
        if data['period'] not in ('day', 'week', 'month'):
            raise ValueError(
                "Incorrect period. ('day','week','month') is allowed")

    def _required(self, data):
        """
        Required data to send
        :param data:
        :return: parameters to send
        """
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

        return params
