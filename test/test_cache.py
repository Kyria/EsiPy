# -*- encoding: utf-8 -*-
# -- Tests based on pycrest cache tests (as these are the same classes)
# -- https://github.com/pycrest/PyCrest/blob/master/tests/test_pycrest.py
from __future__ import absolute_import

import memcache
import mock
import shutil
import time
import unittest

from esipy.cache import BaseCache
from esipy.cache import DictCache
from esipy.cache import DummyCache
from esipy.cache import FileCache
from esipy.cache import MemcachedCache


class TestBaseCache(unittest.TestCase):
    """ BaseCache test class """

    def setUp(self):
        self.c = BaseCache()

    def test_base_cache_set(self):
        self.assertRaises(NotImplementedError, self.c.get, 'key')

    def test_base_cache_get(self):
        self.assertRaises(NotImplementedError, self.c.set, 'key', 'val')

    def test_base_cache_invalidate(self):
        self.assertRaises(NotImplementedError, self.c.invalidate, 'key')


class TestDictCache(unittest.TestCase):
    """ DictCache test class """

    def setUp(self):
        self.c = DictCache()
        self.c.set('key', True)

    def test_dict_cache_set(self):
        self.assertEqual(self.c._dict['key'][0], True)

    def test_dict_cache_get(self):
        self.assertEqual(self.c.get('key'), True)

    def test_dict_cache_invalidate(self):
        self.c.invalidate('key')
        self.assertIsNone(self.c.get('key'))

    def test_dict_cache_expiry(self):
        self.assertEqual(self.c._dict['key'][0], True)
        self.assertEqual(self.c.get('key'), True)
        self.c._dict['key'] = (True, time.time() - 1)
        self.assertIsNone(self.c.get('key'))
        self.assertNotIn('key', self.c._dict)


class TestDummyCache(unittest.TestCase):
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


class TestFileCache(unittest.TestCase):
    """ Class for testing the filecache """

    def setUp(self):
        shutil.rmtree('tmp', ignore_errors=True)
        self.c = FileCache('tmp')

    def tearDown(self):
        del self.c
        shutil.rmtree('tmp', ignore_errors=True)

    def test_file_cache_set(self):
        self.c.set('key', 'bar')
        self.assertEqual(self.c.get('key'), 'bar')

    def test_file_cache_get(self):
        self.c.set('key', 'bar')
        self.assertEqual(self.c.get('key'), 'bar')

        self.c.set('expired', 'baz', -1)
        self.assertEqual(
            self.c.get('expired', 'default_because_expired'),
            'default_because_expired'
        )
        self.assertEqual(self.c.get('expired'), None)

    def test_file_cache_invalidate(self):
        self.c.set('key', 'bar')
        self.assertEqual(self.c.get('key'), 'bar')
        self.c.invalidate('key')
        self.assertEqual(self.c.get('key'), None)


class TestMemcachedCache(unittest.TestCase):
    """A very basic MemcachedCache TestCase
    Primairy goal of this unittest is to get the coverage up
    to spec. Should probably make use of `mockcache` in the future"""

    def setUp(self):
        memcached = memcache.Client(['127.0.0.1:11211'], debug=0)
        memcached.get = mock.MagicMock(return_value='value')
        self.c = MemcachedCache(memcached)

    def test_memcached_set(self):
        self.c.set('key', 'value')

    def test_memcached_get(self):
        self.assertEqual(self.c.get('key'), 'value')

    def test_memcached_invalidate(self):
        self.c.invalidate('key')

    def test_memcached_invalid_argument(self):
        with self.assertRaises(TypeError):
            MemcachedCache(None)
