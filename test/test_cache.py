# -*- encoding: utf-8 -*-
# -- Tests based on pycrest cache tests (as these are the same classes)
# -- https://github.com/pycrest/PyCrest/blob/master/tests/test_pycrest.py
from __future__ import absolute_import

import errno
import httmock
import mock
import sys
import six
import unittest
import memcache

from esipy.cache import BaseCache
from esipy.cache import DictCache
from esipy.cache import DummyCache
from esipy.cache import FileCache
from esipy.cache import MemcachedCache
from requests.adapters import HTTPAdapter
from requests.models import PreparedRequest
from six.moves import builtins


class TestBaseCache(unittest.TestCase):
    """ BaseCache test class """
    
    def setUp(self):
        self.c = BaseCache()

    def test_base_cache_put(self):
        self.assertRaises(NotImplementedError, self.c.get, 'key')

    def test_base_cache_get(self):
        self.assertRaises(NotImplementedError, self.c.put, 'key', 'val')

    def test_base_cache_invalidate(self):
        self.assertRaises(NotImplementedError, self.c.invalidate, 'key')


class TestDictCache(unittest.TestCase):
    """ DictCache test class """
    
    def setUp(self):
        self.c = DictCache()
        self.c.put('key', True)

    def test_dict_cache_put(self):
        self.assertEqual(self.c._dict['key'], True)

    def test_dict_cache_get(self):
        self.assertEqual(self.c.get('key'), True)

    def test_dict_cache_invalidate(self):
        self.c.invalidate('key')
        self.assertIsNone(self.c.get('key'))
        
        
class TestDummyCache(unittest.TestCase):
    """ DummyCache test class. """
    
    def setUp(self):
        self.c = DummyCache()
        self.c.put('never_stored', True)

    def test_dummy_cache_put(self):
        self.assertNotIn('never_stored', self.c._dict)

    def test_dummy_cache_get(self):
        self.assertEqual(self.c.get('never_stored'), None)

    def test_dummy_cache_invalidate(self):
        self.c.invalidate('never_stored')
        self.assertIsNone(self.c.get('never_stored'))


class TestFileCache(unittest.TestCase):
    """ Class for testing the filecache """

    DIR = '/tmp/TestFileCache'

    @mock.patch('os.path.isdir')
    @mock.patch('os.mkdir')
    @mock.patch('{0}.open'.format(builtins.__name__))
    def setUp(self, open_function, mkdir_function, isdir_function):
        self.c = FileCache(TestFileCache.DIR)
        self.c.put('key', 'value')

    @mock.patch('os.path.isdir', return_value=False)
    @mock.patch('os.mkdir')
    def test_file_cache_init(self, mkdir_function, isdir_function):
        c = FileCache(TestFileCache.DIR)

        # Ensure path has been set
        self.assertEqual(c.path, TestFileCache.DIR)

        # Ensure we checked if the dir was already there
        args, kwargs = isdir_function.call_args
        self.assertEqual((TestFileCache.DIR,), args)

        # Ensure we called mkdir with the right args
        args, kwargs = mkdir_function.call_args
        self.assertEqual((TestFileCache.DIR, 0o700), args)

    def test_file_cache_get_uncached(self):
        # Check non-existant key
        self.assertIsNone(self.c.get('nope'))

    @mock.patch('{0}.open'.format(builtins.__name__))
    def test_file_cache_get_cached(self, open_function):
        self.assertEqual(self.c.get('key'), 'value')

    @unittest.skipIf(six.PY2, 'Python 2.x uses a diffrent protocol')
    @mock.patch('{0}.open'.format(builtins.__name__), mock.mock_open(
        read_data=b'x\x9ck`\ne-K\xcc)M-d\xd0\x03\x00\x17\xde\x03\x99'))
    def test_file_cache_get_cached_file_py3(self):
        del(self.c._cache['key'])
        self.assertEqual(self.c.get('key'), 'value')

    @unittest.skipIf(six.PY3, 'Python 3.x uses a diffrent protocol')
    @mock.patch('{0}.open'.format(builtins.__name__), mock.mock_open(
        read_data='x\x9ck`\ne-K\xcc)M-d\xd0\x03\x00\x17\xde\x03\x99'))
    def test_file_cache_get_cached_file_py2(self):
        del(self.c._cache['key'])
        self.assertEqual(self.c.get('key'), 'value')

    @mock.patch('os.unlink')
    def test_file_cache_invalidate(self, unlink_function):
        # Make sure our key is here in the first place
        self.assertIn('key', self.c._cache)

        # Unset the key and ensure unlink() was called
        self.c.invalidate('key')
        self.assertTrue(unlink_function.called)

    @mock.patch(
        'os.unlink',
        side_effect=OSError(
            errno.ENOENT,
            'No such file or directory')
    )
    def test_file_cache_unlink_exception(self, unlink_function):
        self.assertIsNone(self.c.invalidate('key'))


class TestMemcachedCache(unittest.TestCase):
    """A very basic MemcachedCache TestCase
    Primairy goal of this unittest is to get the coverage up
    to spec. Should probably make use of `mockcache` in the future"""

    def setUp(self):
        memcached = memcache.Client(['127.0.0.1:11211'], debug=0)
        memcached.get = mock.MagicMock(return_value='value')
        self.c = MemcachedCache(memcached)

    def test_memcached_put(self):
        self.c.put('key', 'value')

    def test_memcached_get(self):
        self.assertEqual(self.c.get('key'), 'value')

    def test_memcached_invalidate(self):
        self.c.invalidate('key')

    def test_memcached_invalid_argument(self):
        with self.assertRaises(ValueError):
            MemcachedCache(None)
        
        
if __name__ == "__main__":
    unittest.main()