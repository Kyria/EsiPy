# -*- encoding: utf-8 -*-
""" EsiPy Client """
from __future__ import absolute_import

import time
import warnings
import logging

from concurrent.futures import ThreadPoolExecutor
from collections import namedtuple

import six
from pyswagger.core import BaseClient
from requests import Request
from requests import Session
from requests.exceptions import (
    ConnectionError as RequestsConnectionError, Timeout
)
from requests.adapters import HTTPAdapter

from .events import API_CALL_STATS
from .utils import make_cache_key
from .utils import check_cache
from .utils import get_cache_time_left
from .exceptions import APIException


LOGGER = logging.getLogger(__name__)

# create a named tuple to store the data
CachedResponse = namedtuple(
    'CachedResponse',
    ['status_code', 'headers', 'content', 'url']
)


class EsiClient(BaseClient):
    """ EsiClient is a pyswagger client that override some behavior and
    also add some features like auto retry, parallel calls... """

    __schemes__ = set(['https'])
    __uncached_methods__ = ['POST', 'PUT', 'DELETE', 'HEAD']

    def __init__(self, security=None, retry_requests=False, **kwargs):
        """ Init the ESI client object

        :param security: (optional) the security object [default: None]
        :param retry_requests: (optional) use a retry loop for all requests
        :param headers: (optional) additional headers we want to add
        :param transport_adapter: (optional) an HTTPAdapter object / implement
        :param cache: (optional) esipy.cache.BaseCache cache implementation.
        :param raw_body_only: (optional) default value [False] for all requests
        :param signal_api_call_stats: (optional) allow to define a specific
            signal to use, instead of using the global API_CALL_STATS
        :param timeout: (optional) default value [None=No timeout]
        timeout in seconds for requests

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
            warning_message = (
                "Defining a 'User-Agent' header is a"
                " good practice, and allows CCP to contact you if required."
                " To do this, simply add the following when creating"
                " the client: headers={'User-Agent':'something'}."
            )
            LOGGER.warning(warning_message)
            warnings.warn(warning_message)

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
        self.cache = check_cache(kwargs.pop('cache', False))

        # other
        self.signal_api_call_stats = kwargs.pop(
            'signal_api_call_stats',
            API_CALL_STATS
        )

        self.timeout = kwargs.pop('timeout', None)

    def _retry_request(self, req_and_resp, _retry=0, **kwargs):
        """Uses self._request in a sane retry loop (for 5xx level errors).

        Do not use the _retry parameter, use the same params as _request

        Used when ESIClient is initialized with retry_requests=True
        if raise_on_error is True, this will only raise exception after
        all retry have been done

        """
        raise_on_error = kwargs.pop('raise_on_error', False)

        if _retry:
            # backoff delay loop in seconds: 0.01, 0.16, 0.81, 2.56, 6.25
            time.sleep(_retry ** 4 / 100)

        res = self._request(req_and_resp, **kwargs)

        if 500 <= res.status <= 599:
            _retry += 1
            if _retry < 5:
                LOGGER.warning(
                    "[failure #%d] %s %d: %r",
                    _retry,
                    req_and_resp[0].url,
                    res.status,
                    res.data,
                )
                return self._retry_request(
                    req_and_resp,
                    _retry=_retry,
                    raise_on_error=raise_on_error,
                    **kwargs
                )

        if res.status >= 400 and raise_on_error:
            raise APIException(
                req_and_resp[0].url,
                res.status,
                response=res.raw,
                request_param=req_and_resp[0].query,
                response_header=res.header
            )

        return res

    def multi_request(self, reqs_and_resps, threads=20, **kwargs):
        """Use a threadpool to send multiple requests in parallel.

        :param reqs_and_resps: iterable of req_and_resp tuples
        :param raw_body_only: applied to every request call
        :param opt: applies to every request call
        :param threads: number of concurrent workers to use

        :return: a list of [(pyswagger.io.Request, pyswagger.io.Response), ...]
        """

        opt = kwargs.pop('opt', {})
        raw_body_only = kwargs.pop('raw_body_only', self.raw_body_only)
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

    def _request(self, req_and_resp, **kwargs):
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
        :param raise_on_error: boolean to raise an error if HTTP Code >= 400

        :return: the final response.
        """

        opt = kwargs.pop('opt', {})

        # reset the request and response to reuse existing req_and_resp
        req_and_resp[0].reset()
        req_and_resp[1].reset()

        # required because of inheritance
        request, response = super(EsiClient, self).request(req_and_resp, opt)

        # check cache here so we have all headers, formed url and params
        cache_key = make_cache_key(request)
        res = self.__make_request(request, opt, cache_key)

        if res.status_code == 200:
            self.__cache_response(cache_key, res, request.method.upper())

        # generate the Response object from requests response
        response.raw_body_only = kwargs.pop(
            'raw_body_only',
            self.raw_body_only
        )

        try:
            response.apply_with(
                status=res.status_code,
                header=res.headers,
                raw=six.BytesIO(res.content).getvalue()
            )

        except ValueError:
            # catch JSONDecodeError/ValueError when response is not JSON
            raise APIException(
                request.url,
                res.status_code,
                response=res.content,
                request_param=request.query,
                response_header=res.headers
            )

        if 'warning' in res.headers:
            # send in logger and warnings, so the user doesn't have to use
            # logging to see it (at least once)
            LOGGER.warning("[%s] %s", res.url, res.headers['warning'])
            warnings.warn("[%s] %s" % (res.url, res.headers['warning']))

        if res.status_code >= 400 and kwargs.pop('raise_on_error', False):
            raise APIException(
                request.url,
                res.status_code,
                response=response.raw,
                request_param=request.query,
                response_header=response.header
            )

        return response

    def head(self, req_and_resp, **kwargs):
        """ Take a request_and_response object from pyswagger.App, check
        and prepare everything to make a valid HEAD request

        :param req_and_resp: the request and response object from pyswagger.App
        :param opt: options, see pyswagger/blob/master/pyswagger/io.py#L144
        :param raise_on_error: boolean to raise an error if HTTP Code >= 400

        :return: the final response.
        """

        opt = kwargs.pop('opt', {})

        # reset the request and response to reuse existing req_and_resp
        req_and_resp[0].reset()
        req_and_resp[1].reset()

        # required because of inheritance
        request, response = super(EsiClient, self).request(req_and_resp, opt)

        res = self.__make_request(request, opt, method='HEAD')

        response.apply_with(
            status=res.status_code,
            header=res.headers,
            raw=None,
        )

        if 'warning' in res.headers:
            # send in logger and warnings, so the user doesn't have to use
            # logging to see it (at least once)
            LOGGER.warning("[%s] %s", res.url, res.headers['warning'])
            warnings.warn("[%s] %s" % (res.url, res.headers['warning']))

        if res.status_code >= 400 and kwargs.pop('raise_on_error', False):
            raise APIException(
                request.url,
                res.status_code,
                response='',
                request_param=request.query,
                response_header=response.header
            )

        return response

    def __cache_response(self, cache_key, res, method):
        """ cache the response

        if method is one of self.__uncached_method__, don't cache anything
        """
        if ('expires' in res.headers
                and method not in self.__uncached_methods__):
            cache_timeout = get_cache_time_left(res.headers.get('expires'))

            # Occasionally CCP swagger will return an outdated expire
            # warn and skip cache if timeout is <0
            if cache_timeout >= 0:
                self.cache.set(
                    cache_key,
                    CachedResponse(
                        status_code=res.status_code,
                        headers=res.headers,
                        content=res.content,
                        url=res.url,
                    ),
                )
            else:
                LOGGER.warning(
                    "[%s] returned expired result: %s", res.url,
                    res.headers)
                warnings.warn("[%s] returned expired result" % res.url)

    def __make_request(self, request, opt, cache_key=None, method=None):
        """ Check cache, deal with expiration and etag, make the request and
        return the response or cached response.

        :param request: the pyswagger.io.Request object to prepare the request
        :param opt: options, see pyswagger/blob/master/pyswagger/io.py#L144
        :param cache_key: the cache key used for the cache stuff.
        :param method: [default:None] allows to force the method, especially
            useful if you want to make a HEAD request.
            Default value will use endpoint method

        """
        # check expiration and etags
        opt_headers = {}
        cached_response = self.cache.get(cache_key, None)
        if cached_response is not None:
            # if we have expires cached, and still validd
            expires = cached_response.headers.get('expires', None)
            if expires is not None:
                cache_timeout = get_cache_time_left(
                    cached_response.headers['expires']
                )
                if cache_timeout >= 0:
                    return cached_response

            # if we have etags, add the header to use them
            etag = cached_response.headers.get('etag', None)
            if etag is not None:
                opt_headers['If-None-Match'] = etag

            # if nothing makes us use the cache, invalidate everything
            if (expires is None or cache_timeout < 0) and etag is None:
                self.cache.invalidate(cache_key)

        # apply request-related options before preparation.
        request.prepare(
            scheme=self.prepare_schemes(request).pop(),
            handle_files=False
        )
        request._patch(opt)

        # prepare the request and make it.
        method = method or request.method.upper()
        request.header.update(opt_headers)
        prepared_request = self._session.prepare_request(
            Request(
                method=method,
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
                timeout=self.timeout,
            )

        except (RequestsConnectionError, Timeout) as exc:
            # timeout issue, generate a fake response to finish the process
            # as a normal error 500
            res = CachedResponse(
                status_code=500,
                headers={},
                content=('{"error": "%s"}' % str(exc)).encode('latin-1'),
                url=prepared_request.url
            )

        # event for api call stats
        self.signal_api_call_stats.send(
            url=res.url,
            status_code=res.status_code,
            elapsed_time=time.time() - start_api_call,
            message=res.content if res.status_code != 200 else None
        )

        # if we have HTTP 304 (content didn't change), return the cached
        # response updated with the new headers
        if res.status_code == 304 and cached_response is not None:
            cached_response.headers['Expires'] = res.headers.get('Expires')
            cached_response.headers['Date'] = res.headers.get('Date')
            return cached_response
        return res
