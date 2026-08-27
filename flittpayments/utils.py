from __future__ import absolute_import, unicode_literals
from collections import OrderedDict

import re
import json
import base64
import six.moves.urllib as urllib


def to_b64(data):
    """
    Encoding data string base64 algorithm
    """
    return base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')


def from_b64(data):
    """
    Encoding data string base64 algorithm
    """
    return base64.b64decode(json.dumps(data).encode('utf-8')).decode('utf-8')


def to_json(data):
    """
    to json string
    :param data: params to convert to json
    :return: json string
    """
    return json.dumps(data)


def to_form(data):
    """
    to form string
    :param data: params to convert to form data
    :return: encoded url string
    """
    data = OrderedDict(sorted(data.items()))
    return urllib.parse.urlencode(data)


def merge_dict(x, y):
    """
    :param x: firs dict
    :param y: second dict
    :return: merged dict
    """
    z = x.copy()
    z.update(y)
    return z


def join_url(url, *paths):
    """
    :param url: api url
    :param paths: endpoint
    :return: full url
    """
    for path in paths:
        url = re.sub(r'/?$', re.sub(r'^/?', '/', path), url)
    return url


def from_json(json_string):
    """
    :param json_string: json data string to encode
    :return: data dict
    """
    return json.loads(json_string)


def from_form(form_string):
    """
    :param form_string: form data string to encode
    :return: data dict
    """
    return dict(urllib.parse.parse_qsl(form_string))
