# -*- encoding: utf-8 -*-
# pylint: skip-file
from __future__ import absolute_import

from esipy import EsiApp
from esipy.cache import DictCache
from pyswagger import App

import httmock
import mock
import unittest

from .mock import _swagger_spec_mock_
from .mock import make_expire_time_str
from .mock import make_expired_time_str

import logging
# set pyswagger logger to error, as it displays too much thing for test needs
pyswagger_logger = logging.getLogger('pyswagger')
pyswagger_logger.setLevel(logging.ERROR)


class TestEsiApp(unittest.TestCase):

    ESI_CACHE_PREFIX = 'esipy_test'
    ESI_V1_CACHE_KEY = '%s:app://esi.evetech.net/v1/swagger.json' % (
        ESI_CACHE_PREFIX
    )
    ESI_META_SWAGGER = 'test/resources/meta_swagger.json'
    ESI_V1_SWAGGER = 'test/resources/swagger.json'

    @mock.patch('six.moves.urllib.request.urlopen')
    def setUp(self, urlopen_mock):
        # I hate those mock... thx urlopen instead of requests...
        urlopen_mock.return_value = open(TestEsiApp.ESI_META_SWAGGER)
        with httmock.HTTMock(*_swagger_spec_mock_):
            self.app = EsiApp(cache_prefix='esipy_test')

    @mock.patch('six.moves.urllib.request.urlopen')
    def test_app_op_attribute(self, urlopen_mock):
        self.assertTrue(self.app.op)
        self.assertEqual(
            self.app.op['verify'].url,
            '//esi.evetech.net/verify/'
        )

        urlopen_mock.return_value = open(TestEsiApp.ESI_META_SWAGGER)
        with httmock.HTTMock(*_swagger_spec_mock_):
            app = EsiApp(cache_prefix='esipy_test', cache_time=-1)
            self.assertEqual(app.expire, 86400)

    def test_app_getattr_fail(self):
        with self.assertRaises(AttributeError):
            self.app.doesnotexist

        with self.assertRaises(AttributeError):
            self.app.verify

    @mock.patch('six.moves.urllib.request.urlopen')
    def test_app_invalid_cache_value(self, urlopen_mock):
        cache = DictCache()
        cache.set(self.app.esi_meta_cache_key, 'somerandomvalue')
        urlopen_mock.return_value = open(TestEsiApp.ESI_META_SWAGGER)
        with httmock.HTTMock(*_swagger_spec_mock_):
            EsiApp(cache_prefix='esipy_test', cache=cache)

        self.assertNotEqual(
            cache.get(self.app.esi_meta_cache_key),
            'somerandomvalue'
        )

    @mock.patch('six.moves.urllib.request.urlopen')
    def test_app_getattr_and_cache(self, urlopen_mock):
        with httmock.HTTMock(*_swagger_spec_mock_):
            urlopen_mock.return_value = open(TestEsiApp.ESI_V1_SWAGGER)
            self.assertIsNotNone(
                self.app.cache.get(self.app.esi_meta_cache_key, None)
            )
            self.assertEqual(len(self.app.cache._dict), 1)
            appv1 = self.app.get_v1_swagger

            self.assertTrue(isinstance(appv1, App))
            self.assertEqual(
                self.app.cache.get(self.ESI_V1_CACHE_KEY)[0],
                appv1
            )
            appv1_bis = self.app.get_v1_swagger
            self.assertEqual(appv1, appv1_bis)

            self.app.clear_cached_endpoints()
            self.assertIsNone(
                self.app.cache.get(self.app.esi_meta_cache_key, None)
            )
            self.assertIsNone(self.app.cache.get(self.ESI_V1_CACHE_KEY, None))

            urlopen_mock.return_value = open(TestEsiApp.ESI_META_SWAGGER)
            self.app.op
            self.assertIsNotNone(
                self.app.cache.get(self.app.esi_meta_cache_key, None)
            )

    @mock.patch('six.moves.urllib.request.urlopen')
    def test_app_getattr_no_cache(self, urlopen_mock):
        with httmock.HTTMock(*_swagger_spec_mock_):
            urlopen_mock.return_value = open(TestEsiApp.ESI_META_SWAGGER)
            app_nocache = EsiApp(
                cache=None, cache_prefix=self.ESI_CACHE_PREFIX)

            urlopen_mock.return_value = open(TestEsiApp.ESI_V1_SWAGGER)
            self.assertIsNone(
                app_nocache.cache.get(self.app.esi_meta_cache_key, None)
            )
            appv1 = app_nocache.get_v1_swagger

            self.assertTrue(isinstance(appv1, App))
            self.assertIsNone(
                app_nocache.cache.get(self.ESI_V1_CACHE_KEY, None))

    @mock.patch('six.moves.urllib.request.urlopen')
    def test_app_expired_header_etag(self, urlopen_mock):
        @httmock.all_requests
        def check_etag(url, request):
            self.assertEqual(
                request.headers.get('If-None-Match'),
                '"esipyetag"')
            return httmock.response(
                headers={
                    'Expires': make_expire_time_str(),
                    'Etag': '"esipyetag"'
                },
                status_code=304)

        cache = DictCache()
        with httmock.HTTMock(*_swagger_spec_mock_):
            urlopen_mock.return_value = open(TestEsiApp.ESI_META_SWAGGER)
            self.assertEqual(len(cache._dict), 0)
            app = EsiApp(
                cache_time=None, cache=cache, cache_prefix='esipy_test')
            self.assertEqual(len(cache._dict), 1)

        cache.get(
            app.esi_meta_cache_key
        )[1]['expires'] = make_expired_time_str()
        cached_app = cache.get(app.esi_meta_cache_key)[0]

        with httmock.HTTMock(check_etag):
            urlopen_mock.return_value = open(TestEsiApp.ESI_META_SWAGGER)
            esiapp = EsiApp(
                cache_time=None, cache=cache, cache_prefix='esipy_test')
            self.assertEqual(cached_app, esiapp.app)
            urlopen_mock.return_value.close()

    @mock.patch('six.moves.urllib.request.urlopen')
    def test_app_expired_header_no_etag(self, urlopen_mock):
        cache = DictCache()
        with httmock.HTTMock(*_swagger_spec_mock_):
            urlopen_mock.return_value = open(TestEsiApp.ESI_META_SWAGGER)
            app = EsiApp(
                cache_time=None, cache=cache, cache_prefix='esipy_test')

            urlopen_mock.return_value = open(TestEsiApp.ESI_V1_SWAGGER)
            appv1 = app.get_v1_swagger
            cache.get(self.ESI_V1_CACHE_KEY)[1]['Expires'] = None

            urlopen_mock.return_value = open(TestEsiApp.ESI_V1_SWAGGER)
            appv1_uncached = app.get_v1_swagger
            self.assertNotEqual(appv1, appv1_uncached)

    @mock.patch('six.moves.urllib.request.urlopen')
    def test_app_valid_header_etag(self, urlopen_mock):
        @httmock.all_requests
        def fail_if_request(url, request):
            self.fail('Cached data is not supposed to do requests')

        cache = DictCache()

        with httmock.HTTMock(*_swagger_spec_mock_):
            urlopen_mock.return_value = open(TestEsiApp.ESI_META_SWAGGER)
            EsiApp(cache_time=None, cache=cache, cache_prefix='esipy_test')

        with httmock.HTTMock(fail_if_request):
            urlopen_mock.return_value = open(TestEsiApp.ESI_META_SWAGGER)
            EsiApp(cache_time=None, cache=cache, cache_prefix='esipy_test')
            urlopen_mock.return_value.close()
