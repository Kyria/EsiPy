# -*- encoding: utf-8 -*-
from __future__ import absolute_import

from . import __version__
from .cache import BaseCache
from .cache import DummyCache
from .cache import DictCache

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
        :param auth_offset: (optionnal) time in second to substract to the
        expiry date of the token
        """
        super(EsiClient, self).__init__(security)
        self.security = security
        self._session = Session()
        self.auth_offset = kwargs.pop('auth_offset', 0)

        # check for specified headers and update session.headers
        headers = kwargs.pop('headers', {})
        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'EsiPy/%s' % __version__
        self._session.headers.update({"Accept": "application/json"})
        self._session.headers.update(headers)

        # transport adapter
        transport_adapter = kwargs.pop('headers', None)
        if isinstance(transport_adapter, HTTPAdapter):
            session.mount('http://', transport_adapter)
            session.mount('https://', transport_adapter)

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
                raise ValueError('Provided cache must implement APICache')

    def request(self, req_and_resp, opt=None):
        """ Take a request_and_response object from pyswagger.App and
        check auth, token, headers, prepare the actual request and fill the
        response

        :param req_and_resp: the request and response object from pyswagger.App
        :param opt: options, see pyswagger/blob/master/pyswagger/io.py#L144

        :return: the final response.
        """
        if opt is None:
            opt = {}

        if self.security and self.security.is_token_expired(self.auth_offset):
            self.refresh_auth()

        req, response = super(EsiClient, self).request(req_and_resp, opt)

        # apply request-related options before preparation.
        req.prepare(scheme=self.prepare_schemes(req).pop(), handle_files=False)
        req._patch(opt)

        request = Request(
            method=req.method.upper(),
            url=req.url,
            params=req.query,
            data=req.data,
            headers=req.header
        )
        prepared_request = self._session.prepare_request(request)
        res = self._session.send(
            prepared_request,
            stream=True
        )

        response.apply_with(
            status=res.status_code,
            header=res.headers,
            raw=six.BytesIO(res.content).getvalue()
        )

        return response, res

    def refresh_auth(self):
        """ Update the auth data (tokens) using the refresh token in auth.
        """
        request_data = self.security.get_refresh_token_request_params()
        res = self._session.post(**request_data)
        if res.status_code != 200:
            raise APIException(
                request_data['url'],
                res.status_code,
                res.json()
            )
        self.security.update_token(res.json())
