from __future__ import absolute_import, unicode_literals
from hashlib import sha1, sha512
from flittpayments.configuration import __sign_sep__ as sep
from flittpayments.exceptions import RequestError

import flittpayments.utils as utils
import hmac
import uuid


def get_data(data, req_type):
    """
    :param data: data to prepare
    :param req_type: request type
    :return: prepared data
    """
    if req_type == 'json':
        return utils.to_json(data)
    if req_type == 'form':
        return utils.to_form(data.get('request'))


def get_request_type(req_type):
    """
    :param req_type: request type
    :return: post header
    """
    types = {
        'json': 'application/json; charset=utf-8',
        'form': 'application/x-www-form-urlencoded; charset=utf-8'
    }
    return types.get(req_type, types['json'])


def get_signature(secret_key, params, protocol):
    """
    :param secret_key: merchant secret
    :param params: post params
    :param protocol: api protocol version
    :return: signature string
    """
    if protocol == '2.0':
        str_sign = sep.join([secret_key, params])
        calc_sign = sha1(str_sign.encode('utf-8')).hexdigest()
        return calc_sign
    else:
        data = [secret_key]
        data.extend([str(params[key]) for key in sorted(iter(params.keys()))
                     if params[key] != '' and not params[key] is None])
        return sha1(sep.join(data).encode('utf-8')).hexdigest()


def get_reports_signature(key, application_id, date):
    """
    Signature for the Reports API's token endpoint (portal.flitt.com) -
    a completely separate scheme from get_signature() above: SHA512 over
    key|application_id|date, not SHA1/HMAC over merchant request params.
    :param key: Reports application private key
    :param application_id: Reports application id
    :param date: any string, used only as a signature salt
    :return: sha512 hex digest
    """
    raw = sep.join([str(key), str(application_id), str(date)])
    return sha512(raw.encode('utf-8')).hexdigest()


def get_desc(order_id):
    """
    :param order_id: order id
    :return: description string
    """
    return 'Pay for order #: %s' % order_id


def generate_order_id():
    """
    :return: unic order id
    """
    return str(uuid.uuid4())


def check_data(data):
    """
    :param data: required data
    :return: checking required data not empty
    """
    for key, value in data.items():
        if value == '' or None:
            raise RequestError(key)
        if key == 'amount':
            try:
                int(value)
            except ValueError:
                raise ValueError('Amount must numeric')


def is_valid(data, secret_key, protocol):
    if 'signature' in data:
        result_signature = data['signature']
        del data['signature']
    else:
        raise ValueError('Incorrect data')
    if 'response_signature_string' in data:
        del data['response_signature_string']
    signature = get_signature(secret_key=secret_key,
                              params=data,
                              protocol=protocol)
    return hmac.compare_digest(str(result_signature), str(signature))


def is_approved(data, secret_key, protocol):
    if 'order_status' not in data:
        raise ValueError('Incorrect data')
    if not is_valid(data, secret_key, protocol):
        raise Exception('Payment invalid')
    return data.get('order_status') == 'approved'
