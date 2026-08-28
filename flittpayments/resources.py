from __future__ import absolute_import, unicode_literals
from flittpayments import utils
from flittpayments import exceptions
from flittpayments._compat import resolve

try:
    from contextvars import ContextVar
except ImportError:  # pragma: no cover - Python versions below 3.7
    ContextVar = None

from threading import local
from weakref import WeakKeyDictionary


_UNSET = object()


class Resource(object):
    def __init__(self, api=None, headers=None):
        object.__setattr__(self, 'api', api)
        object.__setattr__(self, '__headers__', headers or {})
        object.__setattr__(self, '_state_local', local())
        state_context = None
        if ContextVar is not None:
            state_context = ContextVar(
                'flittpayments_resource_state_%s' % id(self))
        object.__setattr__(self, '_state_context', state_context)
        self._set_state(data={}, order_id=None)

    def _state(self):
        if self._state_context is not None:
            return self._state_context.get(({}, None))
        task = self._current_task()
        if task is not None:
            return self._task_states().get(task, ({}, None))
        return getattr(self._state_local, 'state', ({}, None))

    def _set_state(self, data=_UNSET, order_id=_UNSET):
        current_data, current_order_id = self._state()
        if data is _UNSET:
            data = current_data
        if order_id is _UNSET:
            order_id = current_order_id
        state = (data, order_id)
        if self._state_context is not None:
            self._state_context.set(state)
            return
        task = self._current_task()
        if task is not None:
            self._task_states()[task] = state
            return
        self._state_local.state = state

    def _task_states(self):
        states = getattr(self._state_local, 'task_states', None)
        if states is None:
            states = WeakKeyDictionary()
            self._state_local.task_states = states
        return states

    @staticmethod
    def _current_task():
        try:
            import asyncio
            current_task = getattr(asyncio, 'current_task', None)
            if current_task is None:
                current_task = asyncio.Task.current_task
            return current_task()
        except (AttributeError, ImportError, RuntimeError):
            return None

    def _data(self):
        return self._state()[0]

    @property
    def __data__(self):
        """Backward-compatible view of task-local response data."""
        return self._data()

    @__data__.setter
    def __data__(self, value):
        self._set_state(data=value)

    @property
    def order_id(self):
        return self._state()[1]

    @order_id.setter
    def order_id(self, value):
        self._set_state(order_id=value)

    def __str__(self):
        return self._data().__str__()

    def __repr__(self):
        return self._data().__str__()

    def __getattr__(self, name):
        try:
            return self._data()[name]
        except KeyError:
            return object.__getattribute__(self, name)

    def __contains__(self, name):
        return name in self._data()

    def get_url(self):
        if 'checkout_url' in self._data():
            return self.__getattr__('checkout_url')

    def response(self, response, order_id=_UNSET):
        """
        :param response: api response
        :param order_id: order id associated with this request, if any
        :return: result
        """
        return resolve(
            response,
            lambda value: self._parse_response(value, order_id)
        )

    def _parse_response(self, response, order_id=_UNSET):
        """Parse a resolved sync or async API response."""
        try:
            result = None
            if self.api.request_type == 'json':
                result = utils.from_json(response).get('response', '')
            if self.api.request_type == 'form':
                result = utils.from_form(response)
            return self._get_result(result, order_id)
        except KeyError:
            raise ValueError('Undefined format error.')

    def _get_result(self, result, order_id=_UNSET):
        """
        in some api param response_status not exist...
        :param result: api result
        :return: exception
        """
        if 'error_message' in result:
            raise exceptions.ResponseError(result)
        if 'data' in result and self.api.api_protocol == '2.0':
            result['data'] = utils.from_b64(result['data'])
        self._set_state(data=result, order_id=order_id)
        return result
