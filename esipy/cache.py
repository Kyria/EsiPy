# -*- encoding: utf-8 -*-
""" Cache objects for EsiPy """
import hashlib
import logging

try:
    import pickle
except ImportError:  # pragma: no cover
    import cPickle as pickle

LOGGER = logging.getLogger(__name__)


def _hash(data):
    """ generate a hash from data object to be used as cache key """
    hash_algo = hashlib.new('md5')
    hash_algo.update(pickle.dumps(data))
    # prefix allows possibility of multiple applications
    # sharing same keyspace
    return 'esi_' + hash_algo.hexdigest()


class BaseCache(object):
    """ Base cache 'abstract' object that defined
    the cache methods used in esipy
    """

    def set(self, key, value):
        """ Set a value in the cache. """
        raise NotImplementedError

    def get(self, key, default=None):
        """ Get a value in the cache, return default if not exist """
        raise NotImplementedError

    def invalidate(self, key):
        """ Invalidate a cache key """
        raise NotImplementedError


class FileCache(BaseCache):
    """ BaseCache implementation using files to store the data.
    This implementation uses diskcache.Cache
    see http://www.grantjenks.com/docs/diskcache/api.html#cache for more
    informations

    This cache requires you to install diskcache using `pip install diskcache`
    """

    def __init__(self, path, **settings):
        """ Constructor

        Arguments:
            path {String} -- The path on the disk to save the data
            settings {dict} -- The settings values for diskcache
        """
        from diskcache import Cache
        self._cache = Cache(path, **settings)

    def __del__(self):
        """ Close the connection as the cache instance is deleted.
        Safe to use as there are no circular ref.
        """
        self._cache.close()

    def set(self, key, value):
        self._cache.set(_hash(key), value)

    def get(self, key, default=None):
        return self._cache.get(_hash(key), default)

    def invalidate(self, key):
        self._cache.delete(_hash(key))


class DictCache(BaseCache):
    """ BaseCache implementation using Dict to store the cached data. """

    def __init__(self):
        self._dict = {}

    def get(self, key, default=None):
        return self._dict.get(key, default)

    def set(self, key, value):
        self._dict[key] = value

    def invalidate(self, key):
        self._dict.pop(key, None)


class DummyCache(BaseCache):
    """ Base cache implementation that provide a fake cache that
    allows a "no cache" use without breaking everything """

    def __init__(self):
        self._dict = {}

    def get(self, key, default=None):
        return default

    def set(self, key, value):
        pass

    def invalidate(self, key):
        pass


class MemcachedCache(BaseCache):
    """ Base cache implementation for memcached.

    This cache requires you to install memcached using
    `pip install python-memcached`
    """

    def __init__(self, memcache_client):
        """ memcache_client must be an instance of memcache.Client().
        """
        import memcache
        if not isinstance(memcache_client, memcache.Client):
            raise TypeError('cache must be an instance of memcache.Client')
        self._mc = memcache_client

    def get(self, key, default=None):
        value = self._mc.get(_hash(key))
        return value if value is not None else default

    def set(self, key, value):
        return self._mc.set(_hash(key), value)

    def invalidate(self, key):
        return self._mc.delete(_hash(key))


class RedisCache(BaseCache):
    """ BaseCache implementation for Redis cache.

    This cache handler requires the redis package to be installed
    `pip install redis`
    """

    def __init__(self, redis_client):
        """ redis_client must be an instance of redis.Redis"""
        from redis import Redis
        if not isinstance(redis_client, Redis):
            raise TypeError('cache must be an instance of redis.Redis')
        self._r = redis_client

    def get(self, key, default=None):
        value = self._r.get(_hash(key))
        return pickle.loads(value) if value is not None else default

    def set(self, key, value):
        return self._r.set(_hash(key), pickle.dumps(value))

    def invalidate(self, key):
        return self._r.delete(_hash(key))
