# -*- encoding: utf-8 -*-
import hashlib
import zlib
import os

try:
    import pickle
except ImportError:  # pragma: no cover
    import cPickle as pickle

import logging
logger = logging.getLogger("esipy.cache")


class BaseCache(object):
    """ Base cache 'abstract' object that defined
    the cache methods used in esipy
    """

    def put(self, key, value):
        raise NotImplementedError

    def get(self, key):
        raise NotImplementedError

    def invalidate(self, key):
        raise NotImplementedError

    def _hash(self, data):
        h = hashlib.new('md5')
        h.update(pickle.dumps(data))
        # prefix allows possibility of multiple applications
        # sharing same keyspace
        return 'pyc_' + h.hexdigest()


class FileCache(BaseCache):
    """ BaseCache implementation using files to store the data.
    This implementation is 'persistent' as data are stored on the
    disc and not only in the memory
    """

    def __init__(self, path):
        self._cache = {}
        self.path = path
        if not os.path.isdir(self.path):
            os.mkdir(self.path, 0o700)

    def _getpath(self, key):
        return os.path.join(self.path, self._hash(key) + '.cache')

    def put(self, key, value):
        with open(self._getpath(key), 'wb') as f:
            f.write(
                zlib.compress(
                    pickle.dumps(value,
                                 pickle.HIGHEST_PROTOCOL)))
        self._cache[key] = value

    def get(self, key):
        if key in self._cache:
            return self._cache[key]

        try:
            with open(self._getpath(key), 'rb') as f:
                return pickle.loads(zlib.decompress(f.read()))
        except IOError as ex:
            logger.debug('IOError: {0}'.format(ex))
            if ex.errno == 2:  # file does not exist (yet)
                return None
            else:   # pragma: no cover
                raise

    def invalidate(self, key):
        self._cache.pop(key, None)

        try:
            os.unlink(self._getpath(key))
        except OSError as ex:
            if ex.errno == 2:  # does not exist
                pass
            else:   # pragma: no cover
                raise


class DictCache(BaseCache):
    """ BaseCache implementation using Dict to store the cached data. """

    def __init__(self):
        self._dict = {}

    def get(self, key):
        return self._dict.get(key, None)

    def put(self, key, value):
        self._dict[key] = value

    def invalidate(self, key):
        self._dict.pop(key, None)


class DummyCache(BaseCache):
    """ Base cache implementation that provide a fake cache that
    allows a "no cache" use without breaking everything """
    def __init__(self):
        self._dict = {}

    def get(self, key):
        return None

    def put(self, key, value):
        pass

    def invalidate(self, key):
        pass


class MemcachedCache(BaseCache):
    """ Base cache implementation for memcached. """

    def __init__(self, memcache_client):
        """ memcache_client must be an instance of memcache.Client().
        """
        import memcache
        if not isinstance(memcache_client, memcache.Client):
            raise ValueError('cache must be an instance of memcache.Client')
        self._mc = memcache_client

    def get(self, key):
        return self._mc.get(self._hash(key))

    def put(self, key, value):
        return self._mc.set(self._hash(key), value)

    def invalidate(self, key):
        return self._mc.delete(self._hash(key))
