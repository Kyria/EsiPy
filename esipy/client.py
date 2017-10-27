# -*- encoding: utf-8 -*-
from __future__ import absolute_import

from .cache import BaseCache
from .cache import DictCache
from .cache import DummyCache
from .events import api_call_stats

from collections import namedtuple
from datetime import datetime
from email.utils import parsedate
from pyswagger.core import BaseClient
from requests import Request
from requests import Session
from requests.exceptions import (
    ConnectionError as RequestsConnectionError, Timeout
)
from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor

import time
import six
import warnings
import logging

logger = logging.getLogger(__name__)

# create a named tuple to store the data
CachedResponse = namedtuple(
    'CachedResponse',
    ['status_code', 'headers', 'content', 'url']
)


class EsiClient(BaseClient):
    __schemes__ = set(['https'])

    __image_server__ = {
        'singularity': 'https://image.testeveonline.com/',
        'tranquility': 'https://imageserver.eveonline.com/',
    }

    def __init__(self, security=None, retry_requests=False, **kwargs):
        """ Init the ESI client object

        :param security: (optional) the security object [default: None]
        :param retry_requests: (optional) use a retry loop for all requests
        :param headers: (optional) additional headers we want to add
        :param transport_adapter: (optional) an HTTPAdapter object / implement
        :param cache: (optional) esipy.cache.BaseCache cache implementation.
        :param raw_body_only: (optional) default value [False] for all requests

        """
        super(EsiClient, self).__init__(security)
        self.security = security
        self._session = Session()

        # set the proper request implementation
        if retry_requests:
            self.request = self._retry_request
        else:
            self.request = self._request

        # store default raw_body_only in case user never want parsing
        self.raw_body_only = kwargs.pop('raw_body_only', False)

        # check for specified headers and update session.headers
        headers = kwargs.pop('headers', {})
        if 'User-Agent' not in headers:
            headers['User-Agent'] = (
                'EsiPy/Client - '
                'https://github.com/Kyria/EsiPy'
            )
        self._session.headers.update({"Accept": "application/json"})
        self._session.headers.update(headers)

        # transport adapter
        transport_adapter = kwargs.pop('transport_adapter', None)
        if isinstance(transport_adapter, HTTPAdapter):
            self._session.mount('http://', transport_adapter)
            self._session.mount('https://', transport_adapter)

        # initiate the cache object
        if 'cache' not in kwargs:
            self.cache = DictCache()
        else:
            cache = kwargs.pop('cache')
            if isinstance(cache, BaseCache):
                self.cache = cache
            elif cache is None:
                self.cache = DummyCache()
            else:
                raise ValueError('Provided cache must implement BaseCache')

    def _retry_request(self, req_and_resp, _retry=0, **kwargs):
        """Uses self._request in a sane retry loop (for 5xx level errors).

        Do not use the _retry parameter, use the same params as _request

        Used when ESIClient is initialized with retry_requests=True
        """

        if _retry:
            # backoff delay loop in seconds: 0.01, 0.16, 0.81, 2.56, 6.25
            time.sleep(_retry ** 4 / 100)

        res = self._request(req_and_resp, **kwargs)

        if 500 <= res.status <= 599:
            _retry += 1
            if _retry < 5:
                logger.warning(
                    "[failure #%d] %s %d: %r",
                    _retry,
                    res._Response__path,
                    res.status,
                    res.data,
                )
                return self._retry_request(
                    req_and_resp,
                    _retry=_retry,
                    **kwargs
                )

        return res

    def multi_request(self, reqs_and_resps, raw_body_only=None, opt=None,
                      threads=20):
        """Use a threadpool to send multiple requests in parallel.

        :param reqs_and_resps: iterable of req_and_resp tuples
        :param raw_body_only: applied to every request call
        :param opt: applies to every request call
        :param threads: number of concurrent workers to use

        :return: a list of [(pyswagger.io.Request, pyswagger.io.Response), ...]
        """

        # you shouldnt need more than 100, 20 is probably fine in most cases
        threads = max(min(threads, 100), 1)

        def _multi_shim(req_and_resp):
            """Shim self.request to also return the original request."""

            return req_and_resp[0], self.request(
                req_and_resp,
                raw_body_only=raw_body_only,
                opt=opt,
            )

        results = []

        with ThreadPoolExecutor(max_workers=threads) as pool:
            for result in pool.map(_multi_shim, reqs_and_resps):
                results.append(result)

        return results

    def _request(self, req_and_resp, raw_body_only=None, opt=None):
        """ Take a request_and_response object from pyswagger.App and
        check auth, token, headers, prepare the actual request and fill the
        response

        Note on performance : if you need more performance (because you are
        using this in a batch) you'd rather set raw_body_only=True, as parsed
        body is really slow. You'll then have to get data from response.raw
        and convert it to json using "json.loads(response.raw)"

        :param req_and_resp: the request and response object from pyswagger.App
        :param raw_body_only: define if we want the body to be parsed as object
                              instead of staying a raw dict. [Default: False]
        :param opt: options, see pyswagger/blob/master/pyswagger/io.py#L144

        :return: the final response.
        """

        if opt is None:
            opt = {}

        # reset the request and response to reuse existing req_and_resp
        base_request, base_response = req_and_resp
        base_request.reset()
        base_response.reset()

        # required because of inheritance
        request, response = super(EsiClient, self).request(
            (base_request, base_response),
            opt
        )

        # check cache here so we have all headers, formed url and params
        cache_key = self.__make_cache_key(request)
        cached_response = self.cache.get(cache_key, None)

        if cached_response is not None:
            res = cached_response

        else:
            # apply request-related options before preparation.
            request.prepare(
                scheme=self.prepare_schemes(request).pop(),
                handle_files=False
            )
            request._patch(opt)

            # prepare the request and make it.
            prepared_request = self._session.prepare_request(
                Request(
                    method=request.method.upper(),
                    url=request.url,
                    params=request.query,
                    data=request.data,
                    headers=request.header
                )
            )
            start_api_call = time.time()

            try:
                res = self._session.send(
                    prepared_request,
                    stream=True
                )

            except (RequestsConnectionError, Timeout) as e:
                # timeout issue, generate a fake response to finish the process
                # as a normal error 500
                res = CachedResponse(
                    status_code=500,
                    headers={},
                    content=('{"error": "%s"}' % str(e)).encode('latin-1'),
                    url=prepared_request.url
                )

            # event for api call stats
            api_call_stats.send(
                url=res.url,
                status_code=res.status_code,
                elapsed_time=time.time() - start_api_call,
                message=res.content if res.status_code != 200 else None
            )

            if res.status_code == 200:
                self.__cache_response(cache_key, res)

        if raw_body_only is None:
            response.raw_body_only = self.raw_body_only
        else:
            response.raw_body_only = raw_body_only

        response.apply_with(
            status=res.status_code,
            header=res.headers,
            raw=six.BytesIO(res.content).getvalue()
        )

        if 'warning' in res.headers:
            # send in logger and warnings, so the user doesn't have to use
            # logging to see it (at least once)
            logger.warning("[%s] %s" % (res.url, res.headers['warning']))
            warnings.warn("[%s] %s" % (res.url, res.headers['warning']))

        return response

    def __cache_response(self, cache_key, res):
        if 'expires' in res.headers:
            # this date is ALWAYS in UTC (RFC 7231)
            epoch = datetime(1970, 1, 1)
            expire = (
                datetime(
                    *parsedate(res.headers['expires'])[:6]
                ) - epoch
            ).total_seconds()
            now = (datetime.utcnow() - epoch).total_seconds()
            cache_timeout = int(expire) - int(now)

            self.cache.set(
                cache_key,
                CachedResponse(
                    status_code=res.status_code,
                    headers=res.headers,
                    content=res.content,
                    url=res.url,
                ),
                cache_timeout,
            )

    def __make_cache_key(self, request):
        headers = frozenset(request._p['header'].items())
        path = frozenset(request._p['path'].items())
        query = frozenset(request._p['query'])
        return (request.url, headers, path, query)
