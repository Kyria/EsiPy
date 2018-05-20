# -*- encoding: utf-8 -*-
# pylint: skip-file
from __future__ import absolute_import

import memcache
import redis
import shutil
import unittest

from collections import namedtuple

from esipy.cache import BaseCache
from esipy.cache import DictCache
from esipy.cache import DummyCache
from esipy.cache import FileCache
from esipy.cache import MemcachedCache
from esipy.cache import RedisCache

CachedResponse = namedtuple(
    'CachedResponse',
    ['status_code', 'headers', 'content', 'url']
)


class BaseTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(BaseTest, self).__init__(*args, **kwargs)

        # example of simple data
        self.ex_str = ('eve', 'online')
        self.ex_int = ('int', 12345)
        # tuple of frozenset in key, namedtuple in value
        self.ex_cpx = (
            (
                frozenset([('foo', 'bar'), ('int', 2)]),
                frozenset([('header', 'bla')]),
            ),
            CachedResponse(
                status_code=200,
                headers={'foo', 'bar'},
                content='SomeContent'.encode('latin-1'),
                url='http://example.com'
            )
        )

    def check_complex(self, cplx):
        self.assertTrue(isinstance(cplx, CachedResponse))
        self.assertEqual(cplx.status_code, self.ex_cpx[1].status_code)
        self.assertEqual(cplx.headers, self.ex_cpx[1].headers)
        self.assertEqual(cplx.content, self.ex_cpx[1].content)
        self.assertEqual(cplx.url, self.ex_cpx[1].url)


class TestBaseCache(BaseTest):
    """ BaseCache test class """

    def setUp(self):
        self.c = BaseCache()

    def test_base_cache_set(self):
        self.assertRaises(NotImplementedError, self.c.get, 'key')

    def test_base_cache_get(self):
        self.assertRaises(NotImplementedError, self.c.set, 'key', 'val')

    def test_base_cache_invalidate(self):
        self.assertRaises(NotImplementedError, self.c.invalidate, 'key')


class TestDictCache(BaseTest):
    """ DictCache test class """

    def setUp(self):
        self.c = DictCache()
        self.c.set(*self.ex_str)
        self.c.set(*self.ex_int)
        self.c.set(*self.ex_cpx)

    def tearDown(self):
        self.c.invalidate(self.ex_str[0])
        self.c.invalidate(self.ex_int[0])
        self.c.invalidate(self.ex_cpx[0])

    def test_dict_cache_set(self):
        self.assertEqual(self.c._dict[self.ex_str[0]], self.ex_str[1])
        self.assertEqual(self.c._dict[self.ex_int[0]], self.ex_int[1])
        self.assertEqual(self.c._dict[self.ex_cpx[0]], self.ex_cpx[1])

    def test_dict_cache_get(self):
        self.check_complex(self.c.get(self.ex_cpx[0]))

    def test_dict_cache_invalidate(self):
        self.c.invalidate(self.ex_cpx[0])
        self.assertIsNone(self.c.get(self.ex_cpx[0]))


class TestDummyCache(BaseTest):
    """ DummyCache test class. """

    def setUp(self):
        self.c = DummyCache()
        self.c.set('never_stored', True)

    def test_dummy_cache_set(self):
        self.assertNotIn('never_stored', self.c._dict)

    def test_dummy_cache_get(self):
        self.assertEqual(self.c.get('never_stored'), None)

    def test_dummy_cache_invalidate(self):
        self.c.invalidate('never_stored')
        self.assertIsNone(self.c.get('never_stored'))


class TestFileCache(BaseTest):
    """ Class for testing the filecache """

    def setUp(self):
        shutil.rmtree('tmp', ignore_errors=True)
        self.c = FileCache('tmp')

    def tearDown(self):
        del self.c
        shutil.rmtree('tmp', ignore_errors=True)

    def test_file_cache_get_set(self):
        self.c.set(*self.ex_str)
        self.c.set(*self.ex_int)
        self.c.set(*self.ex_cpx)
        self.assertEqual(self.c.get(self.ex_str[0]), self.ex_str[1])
        self.assertEqual(self.c.get(self.ex_int[0]), self.ex_int[1])
        self.check_complex(self.c.get(self.ex_cpx[0]))

    def test_file_cache_update(self):
        self.c.set(
            self.ex_cpx[0],
            CachedResponse(
                status_code=200,
                headers={'foo', 'test'},
                content='Nothing'.encode('latin-1'),
                url='http://foobarbaz.com'
            )
        )
        self.c.set(*self.ex_cpx)
        self.check_complex(self.c.get(self.ex_cpx[0]))

    def test_file_cache_invalidate(self):
        self.c.set('key', 'bar')
        self.assertEqual(self.c.get('key'), 'bar')
        self.c.invalidate('key')
        self.assertEqual(self.c.get('key'), None)


class TestMemcachedCache(BaseTest):
    """ Memcached tests """

    def setUp(self):
        memcached = memcache.Client(['localhost:11211'], debug=0)
        self.c = MemcachedCache(memcached)

    def tearDown(self):
        self.c.invalidate(self.ex_str[0])
        self.c.invalidate(self.ex_int[0])
        self.c.invalidate(self.ex_cpx[0])
        self.c._mc.disconnect_all()

    def test_memcached_get_set(self):
        self.c.set(*self.ex_str)
        self.c.set(*self.ex_int)
        self.c.set(*self.ex_cpx)
        self.assertEqual(self.c.get(self.ex_str[0]), self.ex_str[1])
        self.assertEqual(self.c.get(self.ex_int[0]), self.ex_int[1])
        self.check_complex(self.c.get(self.ex_cpx[0]))

    def test_memcached_update(self):
        self.c.set(
            self.ex_cpx[0],
            CachedResponse(
                status_code=200,
                headers={'foo', 'test'},
                content='Nothing'.encode('latin-1'),
                url='http://foobarbaz.com'
            )
        )
        self.c.set(*self.ex_cpx)
        self.check_complex(self.c.get(self.ex_cpx[0]))

    def test_memcached_invalidate(self):
        self.c.set(*self.ex_str)
        self.assertEqual(self.c.get(self.ex_str[0]), self.ex_str[1])
        self.c.invalidate(self.ex_str[0])
        self.assertEqual(self.c.get(self.ex_str[0]), None)

    def test_memcached_invalid_argument(self):
        with self.assertRaises(TypeError):
            MemcachedCache(None)


class TestRedisCache(BaseTest):
    """RedisCache tests"""

    def setUp(self):
        redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.c = RedisCache(redis_client)

    def tearDown(self):
        self.c.invalidate(self.ex_str[0])
        self.c.invalidate(self.ex_int[0])
        self.c.invalidate(self.ex_cpx[0])

    def test_redis_get_set(self):
        self.c.set(*self.ex_str)
        self.c.set(*self.ex_int)
        self.c.set(*self.ex_cpx)
        self.assertEqual(self.c.get(self.ex_str[0]), self.ex_str[1])
        self.assertEqual(self.c.get(self.ex_int[0]), self.ex_int[1])
        self.check_complex(self.c.get(self.ex_cpx[0]))

    def test_redis_update(self):
        self.c.set(
            self.ex_cpx[0],
            CachedResponse(
                status_code=200,
                headers={'foo', 'test'},
                content='Nothing'.encode('latin-1'),
                url='http://foobarbaz.com'
            )
        )
        self.c.set(*self.ex_cpx)
        self.check_complex(self.c.get(self.ex_cpx[0]))

    def test_redis_invalidate(self):
        self.c.set(*self.ex_str)
        self.assertEqual(self.c.get(self.ex_str[0]), self.ex_str[1])
        self.c.invalidate(self.ex_str[0])
        self.assertEqual(self.c.get(self.ex_str[0]), None)

    def test_redis_invalid_argument(self):
        with self.assertRaises(TypeError):
            RedisCache(None)
