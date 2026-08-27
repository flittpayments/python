from __future__ import absolute_import, unicode_literals
from flittpayments.configuration import (__api_url__, __protocol__, __r_type__,
                                         __version__)
from flittpayments import exceptions

import os
import re
import requests
import logging
import flittpayments.helpers as helper
import flittpayments.utils as utils

log = logging.getLogger(__name__)

# Field names that must never appear in plaintext in debug logs (PAN/CVV/
# IBAN data). This only affects what gets written to the log - the actual
# outbound/inbound payload is untouched.
_SENSITIVE_FIELDS = ('card_number', 'cvv2', 'receiver_iban')


def _mask_sensitive(text):
    """
    Redact sensitive payment fields from a serialized request/response
    body (json/form) before it is written to the debug log.
    :param text: serialized data string, or None
    :return: masked string safe for logging
    """
    if not text:
        return text
    masked = text
    for field in _SENSITIVE_FIELDS:
        masked = re.sub(r'("%s"\s*:\s*")[^"]*(")' % field,
                        r'\1***\2', masked)
        masked = re.sub(r'(%s=)[^&]*' % field, r'\1***', masked)
    return masked


class Api(object):
    user_agent = 'FlittPay-python-sdk/%s' % __version__

    def __init__(self, **kwargs):
        """
        :param kwargs: args
        :arg merchant_id Merchant id numeric
        :arg secret_key Secret key string
        :arg request_type request type allowed json, form
        :arg api_domain api domain
        :arg api_protocol allowed protocols 1.0, 2.0
        :arg timeout request timeout in seconds, default 30
        """
        self.merchant_id = kwargs.get('merchant_id', '')
        self.secret_key = kwargs.get('secret_key', '')
        self.request_type = kwargs.get('request_type', __r_type__)
        self.timeout = kwargs.get('timeout', 30)
        if not self.merchant_id or not self.secret_key:
            self.merchant_id = os.environ.get('CLOUDIPSP_MERCHANT_ID', '')
            self.secret_key = os.environ.get('CLOUDIPSP_SECRETKEY', '')
        domain = kwargs.get('api_domain', 'pay.flitt.com')
        self.api_url = __api_url__.format(api_domain=domain)
        self.api_protocol = kwargs.get('api_protocol', __protocol__)
        if self.api_protocol not in ('1.0', '2.0'):
            raise ValueError('Incorrect protocol version')
        if self.request_type not in ('json', 'form'):
            raise ValueError(
                "Unsupported request_type '%s' (allowed: json, form). "
                "XML support was removed in v2.0." % self.request_type)
        if self.api_protocol == '2.0' and self.request_type != 'json':
            raise ValueError('In protocol \'2.0\' only json allowed')

    def _headers(self):
        """
        :return: request headers
        """
        return {
            'User-Agent': self.user_agent,
            'Content-Type': helper.get_request_type(self.request_type),
        }

    def _request(self, url, method, data, headers):
        """
        :param url: request url
        :param method: request method, POST default
        :param data: request data
        :param headers: request headers
        :return: api response
        """
        log.debug('Request Type: %s' % self.request_type)
        log.debug('URL: %s' % url)
        log.debug('Data: %s' % _mask_sensitive(str(data)))
        log.debug('Headers: %s' % str(headers))

        response = requests.request(method, url, data=data, headers=headers,
                                    timeout=self.timeout)
        return self._response(response, response.content.decode('utf-8'))

    def _response(self, response, content):
        """
        :param response: api response
        :param content: api response body
        :return: if response header 200 or 201 return response data
        """
        status = response.status_code

        log.debug('Status: %s' % str(status))
        log.debug('Content: %s' % _mask_sensitive(content))

        if status in (200, 201):
            return content

        raise exceptions.ServiceError(
            'Response code is: {status}'.format(status=status))

    def post(self, url, data=None, headers=None):
        """
        :param url: endpoint api url
        :param data: request data
        :param headers: request headers
        :return: request
        """
        log.debug('Protocol version: %s' % self.request_type)
        data = data if data is not None else {}

        if 'merchant_id' not in data:
            data['merchant_id'] = self.merchant_id
        if 'reservation_data' in data:
            data['reservation_data'] = utils.to_b64(
                data['reservation_data'])

        if self.api_protocol == '2.0':
            b64_data = utils.to_b64({'order': data})
            data_v2 = {
                'data': b64_data,
                'version': self.api_protocol,
                'signature': helper.get_signature(self.secret_key,
                                                  b64_data,
                                                  self.api_protocol)
            }
            data_string = utils.to_json({'request': data_v2})
        else:
            if 'signature' not in data:
                data['signature'] = helper.get_signature(self.secret_key,
                                                         data,
                                                         self.api_protocol)
            data_string = helper.get_data({'request': data}, self.request_type)

        return self._request(
            utils.join_url(self.api_url, url), 'POST',
            data=data_string,
            headers=utils.merge_dict(headers, self._headers()))
