# -*- encoding: utf-8 -*-
from __future__ import absolute_import

from .cache import BaseCache
from .cache import DictCache
from .cache import DummyCache

from collections import namedtuple
from datetime import datetime
from email.utils import parsedate
from pyswagger.core import BaseClient
from requests import Request
from requests import Session
from requests.adapters import HTTPAdapter


import six


class EsiClient(BaseClient):

    __schemes__ = set(['https'])

    __image_server__ = {
        'singularity': 'https://image.testeveonline.com/',
        'tranquility': 'https://imageserver.eveonline.com/',
    }

    def __init__(
            self,
            security=None,
            **kwargs):
        """ Init the ESI client object

        :param security: (optionnal) the security object [default: None]
        :param headers: (optionnal) additional headers we want to add
        :param transport_adapter: (optionnal) an HTTPAdapter object / implement
        :param cache: (optionnal) esipy.cache.BaseCache cache implementation.
        expiry date of the token
        """
        super(EsiClient, self).__init__(security)
        self.security = security
        self._session = Session()

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

    def request(self, req_and_resp, raw_body_only=False, opt={}):
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
        # required because of inheritance
        request, response = super(EsiClient, self).request(req_and_resp, opt)

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

            res = self._session.send(
                prepared_request,
                stream=True
            )

            if res.status_code == 200:
                self.__cache_response(cache_key, res)

        response.raw_body_only = raw_body_only
        response.apply_with(
            status=res.status_code,
            header=res.headers,
            raw=six.BytesIO(res.content).getvalue()
        )

        return response

    def __cache_response(self, cache_key, res):
        if 'expires' in res.headers:
            # this date is ALWAYS in UTC (RFC 7231)
            #
            epoch = datetime(1970, 1, 1)
            expire = (
                datetime(
                    *parsedate(res.headers['expires'])[:6]
                ) - epoch
            ).total_seconds()
            now = (datetime.utcnow() - epoch).total_seconds()
            cache_timeout = int(expire) - int(now)

        else:
            # if no expire, define that there is no cache
            # -1 will be now -1sec, so it'll expire
            cache_timeout = -1

        # create a named tuple to store the data
        CachedResponse = namedtuple(
            'CachedResponse',
            ['status_code', 'headers', 'content']
        )
        self.cache.set(
            cache_key,
            CachedResponse(
                status_code=res.status_code,
                headers=res.headers,
                content=res.content,
            ),
            cache_timeout,
        )

    def __make_cache_key(self, request):
        headers = frozenset(request._p['header'].items())
        path = frozenset(request._p['path'].items())
        query = frozenset(request._p['query'])
        return (request.url, headers, path, query)
