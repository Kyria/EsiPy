# -*- encoding: utf-8 -*-
""" App entry point. Uses Esi Meta Endpoint to work """
from pyswagger import App

from .utils import check_cache


class EsiApp(object):
    """ EsiApp is an app object that'll allows us to play with ESI Meta
    API, not to have to deal with all ESI versions manually / meta """

    def __init__(self, **kwargs):
        """ Constructor.

        :param: cache if specified, use that cache, else use DictCache
        :param: cache_time is the minimum cache time for versions
        endpoints. If set to 0, never expires". Default 86400sec (1day)
        :param: cache_prefix the prefix used to all cache key for esiapp
        """
        self.meta_url = kwargs.pop(
            'meta_url',
            'https://esi.evetech.net/swagger.json'
        )
        cache_time = kwargs.pop('cache_time', 86400)
        if cache_time == 0 or cache_time is None:
            self.expire = None
        else:
            self.expire = cache_time if cache_time > 0 else 86400

        self.cache_prefix = kwargs.pop('cache_prefix', 'esipy')
        self.esi_meta_cache_key = '%s:app:meta_swagger_url' % self.cache_prefix

        cache = kwargs.pop('cache', False)
        self.caching = True if cache is not None else False
        self.cache = check_cache(cache)

        self.app = self.__get_or_create_app(
            self.meta_url,
            self.esi_meta_cache_key
        )

    def __get_or_create_app(self, app_url, cache_key):
        """ Get the app from cache or generate a new one if required """
        app = self.cache.get(cache_key, None)

        if app is None:
            app = App.create(app_url)
            if self.caching:
                self.cache.set(cache_key, app, self.expire)

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
