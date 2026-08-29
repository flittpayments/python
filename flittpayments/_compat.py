from __future__ import absolute_import, unicode_literals

import inspect


def is_awaitable(value):
    """Return True for native coroutine and awaitable objects."""
    return inspect.isawaitable(value)


async def _resolve_awaitable(value, callback):
    result = callback(await value)
    if inspect.isawaitable(result):
        return await result
    return result


def resolve(value, callback):
    """Apply callback now for sync values, or after an async value resolves."""
    if is_awaitable(value):
        return _resolve_awaitable(value, callback)
    return callback(value)
