from __future__ import absolute_import, unicode_literals

import sys
from abc import ABCMeta, abstractmethod

import six

from flittpayments._compat import resolve


@six.add_metaclass(ABCMeta)
class BaseTransport(object):
    """Abstract HTTP transport used by :class:`flittpayments.Api`."""

    @abstractmethod
    def request(self, method, url, data=None, headers=None, timeout=None):
        """
        Send an HTTP request.

        Implementations must return either a response object or an awaitable
        resolving to one. The response object must expose ``status_code`` and
        ``content`` attributes.
        """
        raise NotImplementedError


class SyncTransport(BaseTransport):
    """Default synchronous transport backed by ``requests``."""

    def __init__(self, session=None):
        if session is None:
            import requests
            session = requests
        self.session = session

    def request(self, method, url, data=None, headers=None, timeout=None):
        return self.session.request(
            method,
            url,
            data=data,
            headers=headers,
            timeout=timeout
        )

    def close(self):
        close = getattr(self.session, 'close', None)
        if close is not None:
            close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class AsyncTransport(BaseTransport):
    """Asynchronous transport backed by ``httpx2.AsyncClient``."""

    def __init__(self, client=None, **client_options):
        if sys.version_info < (3, 10):
            raise RuntimeError(
                'AsyncTransport requires Python 3.10 or newer because httpx2 '
                'does not support this Python version.')
        if client is not None and client_options:
            raise TypeError(
                'client_options cannot be used with a custom client')
        if client is None:
            try:
                import httpx2
            except ImportError:
                raise ImportError(
                    'AsyncTransport requires httpx2. Install it with '
                    'pip install \'flittpayments[async]\'')
            client = httpx2.AsyncClient(**client_options)
        self.client = client

    def request(self, method, url, data=None, headers=None, timeout=None):
        return self.client.request(
            method,
            url,
            content=data,
            headers=headers,
            timeout=timeout
        )

    def aclose(self):
        return self.client.aclose()

    def __aenter__(self):
        return resolve(
            self.client.__aenter__(),
            lambda client: self
        )

    def __aexit__(self, exc_type, exc_value, traceback):
        return self.client.__aexit__(exc_type, exc_value, traceback)


__all__ = ['BaseTransport', 'SyncTransport', 'AsyncTransport']
