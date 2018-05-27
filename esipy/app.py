# -*- encoding: utf-8 -*-
""" App entry point. Uses Esi Meta Endpoint to work """
import time

import requests

from pyswagger import App

from .utils import check_cache
from .utils import get_cache_time_left


class EsiApp(object):
    """ EsiApp is an app object that'll allows us to play with ESI Meta
    API, not to have to deal with all ESI versions manually / meta """

    def __init__(self, **kwargs):
        """ Constructor.

        :param cache: if specified, use that cache, else use DictCache
        :param cache_time: is the minimum cache time for versions
            endpoints. If set to 0, never expires". None uses header expires
            Default 86400 (1d)
        :param cache_prefix: the prefix used to all cache key for esiapp
        :param meta_url: the meta url you want to use. Default is meta esi URL
            https://esi.evetech.net/swagger.json
        :param datasource: the EVE datasource to be used. Default: tranquility
        """
        self.meta_url = kwargs.pop(
            'meta_url',
            'https://esi.evetech.net/swagger.json'
        )
        self.expire = kwargs.pop('cache_time', 86400)
        if self.expire is not None and self.expire < 0:
            self.expire = 86400

        self.cache_prefix = kwargs.pop('cache_prefix', 'esipy')
        self.esi_meta_cache_key = '%s:app:meta_swagger_url' % self.cache_prefix

        cache = kwargs.pop('cache', False)
        self.caching = True if cache is not None else False
        self.cache = check_cache(cache)
        self.datasource = kwargs.pop('datasource', 'tranquility')

        self.app = self.__get_or_create_app(
            self.meta_url,
            self.esi_meta_cache_key
        )

    def __get_or_create_app(self, url, cache_key):
        """ Get the app from cache or generate a new one if required

        Because app object doesn't have etag/expiry, we have to make
        a head() call before, to have these informations first... """
        headers = {"Accept": "application/json"}
        app_url = '%s?datasource=%s' % (url, self.datasource)

        cached = self.cache.get(cache_key, (None, None, 0))
        if cached is None or len(cached) != 3:
            self.cache.invalidate(cache_key)
            cached_app, cached_headers, cached_expiry = (cached, None, 0)
        else:
            cached_app, cached_headers, cached_expiry = cached

        if cached_app is not None and cached_headers is not None:
            # we didn't set custom expire, use header expiry
            expires = cached_headers.get('expires', None)
            cache_timeout = -1
            if self.expire is None and expires is not None:
                cache_timeout = get_cache_time_left(
                    cached_headers['expires']
                )
                if cache_timeout >= 0:
                    return cached_app

            # we set custom expire, check this instead
            else:
                if self.expire == 0 or cached_expiry >= time.time():
                    return cached_app

            # if we have etags, add the header to use them
            etag = cached_headers.get('etag', None)
            if etag is not None:
                headers['If-None-Match'] = etag

            # if nothing makes us use the cache, invalidate it
            if ((expires is None or cache_timeout < 0 or
                 cached_expiry < time.time()) and etag is None):
                self.cache.invalidate(cache_key)

        # set timeout value in case we have to cache it later
        timeout = 0
        if self.expire is not None and self.expire > 0:
            timeout = time.time() + self.expire

        # we are here, we know we have to make a head call...
        res = requests.head(app_url, headers=headers)
        if res.status_code == 304 and cached_app is not None:
            self.cache.set(
                cache_key,
                (cached_app, res.headers, timeout)
            )
            return cached_app

        # ok, cache is not accurate, make the full stuff
        app = App.create(app_url)
        if self.caching:
            self.cache.set(cache_key, (app, res.headers, timeout))

        return app

    def __getattr__(self, name):
        """ Return the request object depending on its nature.

        if "op" is requested, simply return "app.op" which is a pyswagger app
        if anything else is requested, check if it exists, then if it's a
        swagger endpoint, try to create it and return it.
        """
        if name == 'op':
            return self.app.op

        try:
            op_attr = self.app.op[name]
        except KeyError:
            raise AttributeError('%s is not a valid operation' % name)

        # if the endpoint is a swagger spec
        if 'swagger.json' in op_attr.url:
            spec_url = 'https:%s' % op_attr.url
            cache_key = '%s:app:%s' % (self.cache_prefix, op_attr.url)
            return self.__get_or_create_app(spec_url, cache_key)
        else:
            raise AttributeError('%s is not a swagger endpoint' % name)

    def __getattribute__(self, name):
        """ Get attribute. If attribute is app, and app is None, create it
        again from cache / by querying ESI """
        attr = super(EsiApp, self).__getattribute__(name)
        if name == 'app' and attr is None:
            attr = self.__get_or_create_app(
                self.meta_url,
                self.esi_meta_cache_key
            )
            self.app = attr
        return attr

    def clear_cached_endpoints(self, prefix=None):
        """ Invalidate all cached endpoints, meta included

        Loop over all meta endpoints to generate all cache key the
        invalidate each of them. Doing it this way will prevent the
        app not finding keys as the user may change its prefixes
        Meta endpoint will be updated upon next call.
        :param: prefix the prefix for the cache key (default is cache_prefix)
        """
        prefix = prefix if prefix is not None else self.cache_prefix
        for endpoint in self.app.op.values():
            cache_key = '%s:app:%s' % (prefix, endpoint.url)
            self.cache.invalidate(cache_key)
        self.cache.invalidate('%s:app:meta_swagger_url' % self.cache_prefix)
        self.app = None
