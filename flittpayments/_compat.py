from __future__ import absolute_import, unicode_literals

import inspect
import sys


def is_awaitable(value):
    """Return True for native coroutine and awaitable objects."""
    if sys.version_info < (3, 5):
        return False
    return inspect.isawaitable(value)


if sys.version_info >= (3, 5):
    _namespace = {'inspect': inspect}
    exec(
        'async def _resolve_awaitable(value, callback):\n'
        '    result = callback(await value)\n'
        '    if inspect.isawaitable(result):\n'
        '        return await result\n'
        '    return result\n',
        _namespace
    )
    _resolve_awaitable = _namespace['_resolve_awaitable']
else:  # pragma: no cover - exercised only by the legacy tox environments
    _resolve_awaitable = None


def resolve(value, callback):
    """
    Apply callback immediately for sync values, or after awaiting async ones.

    Keeping native ``async def`` syntax inside a runtime-compiled string lets
    the package remain importable on Python 2.7 and Python 3.4 while exposing
    native awaitables on Python 3.5 and newer.
    """
    if is_awaitable(value):
        return _resolve_awaitable(value, callback)
    return callback(value)
