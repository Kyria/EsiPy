# -*- encoding: utf-8 -*-
""" App entry point. Uses Esi Meta Endpoint to work """
from pyswagger import App

from .utils import check_cache


class EsiApp(object):
    """ EsiApp is an app object that'll allows us to play with ESI Meta
    API, not to have to deal with all ESI versions manually / meta """

    ESI_META_URL = 'https://esi.tech.ccp.is/swagger.json'
    ESI_META_CACHE_KEY = 'esipy:meta_swagger_url'

    def __init__(self, **kwargs):
        """ Constructor.

        :param: cache if specified, use that cache, else use DictCache
        :param: cache_time is the minimum cache time for versions
        endpoints. If set to 0, never expires". Default 86400sec (1day)
        """
        cache_time = kwargs.pop('cache_time', 86400)
        if cache_time == 0 or cache_time is None:
            self.expire = None
        else:
            self.expire = cache_time if cache_time > 0 else 86400

        self.cached_version = []

        cache = kwargs.pop('cache', False)
        self.caching = True if cache is not None else False
        self.cache = check_cache(cache)
        self.app = self.__get_or_create_app(
            self.ESI_META_URL,
            self.ESI_META_CACHE_KEY
        )

    def __get_or_create_app(self, app_url, cache_key=None):
        """ Get the app from cache or generate a new one if required """
        if cache_key is None:
            cache_key = app_url
        app = self.cache.get(cache_key, None)

        if app is None:
            app = App.create(app_url)
            if self.caching:
                self.cache.set(cache_key, app, self.expire)
                self.cached_version.append(cache_key)

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
            cache_key = 'esipy:%s' % op_attr.url
            return self.__get_or_create_app(spec_url, cache_key)
        else:
            raise AttributeError('%s is not a swagger endpoint' % name)

    def force_update(self):
        """ update all endpoints by invalidating cache or reloading data """
        for key in self.cached_version:
            self.cache.invalidate(key)
        self.cached_version = []
        self.app = self.__get_or_create_app(
            self.ESI_META_URL,
            self.ESI_META_CACHE_KEY
        )
