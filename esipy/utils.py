# -*- encoding: utf-8 -*-
""" Helper and utils functions """
from datetime import datetime
from email.utils import parsedate

from .cache import BaseCache
from .cache import DictCache
from .cache import DummyCache


def make_cache_key(request):
    """ Generate a cache key from request object data """
    headers = frozenset(request._p['header'].items())
    path = frozenset(request._p['path'].items())
    query = frozenset(request._p['query'])
    return (request.url, headers, path, query)


def check_cache(cache):
    """ check if a cache fits esipy needs or not """
    if isinstance(cache, BaseCache):
        return cache
    elif cache is False:
        return DictCache()
    elif cache is None:
        return DummyCache()
    else:
        raise ValueError('Provided cache must implement BaseCache')


def get_cache_time_left(expires_header):
    """ return the time left in second for an expires header """
    epoch = datetime(1970, 1, 1)
    # this date is ALWAYS in UTC (RFC 7231)
    expire = (
        datetime(
            *parsedate(expires_header)[:6]
        ) - epoch
    ).total_seconds()
    now = (datetime.utcnow() - epoch).total_seconds()
    return int(expire) - int(now)
