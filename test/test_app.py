# -*- encoding: utf-8 -*-
# pylint: skip-file
from __future__ import absolute_import

from esipy import EsiApp
from pyswagger import App

import mock
import unittest

import logging
# set pyswagger logger to error, as it displays too much thing for test needs
pyswagger_logger = logging.getLogger('pyswagger')
pyswagger_logger.setLevel(logging.ERROR)


class TestEsiApp(unittest.TestCase):

    ESI_CACHE_PREFIX = 'esipy_test'
    ESI_V1_CACHE_KEY = '%s:app://esi.evetech.net/v1/swagger.json' % (
        ESI_CACHE_PREFIX
    )

    @mock.patch('six.moves.urllib.request.urlopen')
    def setUp(self, urlopen_mock):
        # I hate those mock... thx urlopen instead of requests...
        urlopen_mock.return_value = open('test/resources/meta_swagger.json')
        self.app = EsiApp(cache_time=None, cache_prefix='esipy_test')

    def test_app_op_attribute(self):
        self.assertTrue(self.app.op)
        self.assertEqual(
            self.app.op['verify'].url,
            '//esi.evetech.net/verify/'
        )

    def test_app_getattr_fail(self):
        with self.assertRaises(AttributeError):
            self.app.doesnotexist

        with self.assertRaises(AttributeError):
            self.app.verify

    @mock.patch('six.moves.urllib.request.urlopen')
    def test_app_getattr_and_cache(self, urlopen_mock):
        urlopen_mock.return_value = open('test/resources/swagger.json')
        self.assertIsNotNone(
            self.app.cache.get(self.app.esi_meta_cache_key, None)
        )
        self.assertEqual(len(self.app.cache._dict), 1)
        appv1 = self.app.get_v1_swagger

        self.assertTrue(isinstance(appv1, App))
        self.assertEqual(self.app.cache.get(self.ESI_V1_CACHE_KEY), appv1)
        appv1_bis = self.app.get_v1_swagger
        self.assertEqual(appv1, appv1_bis)

        self.app.clear_cached_endpoints()
        self.assertIsNone(
            self.app.cache.get(self.app.esi_meta_cache_key, None)
        )
        self.assertIsNone(self.app.cache.get(self.ESI_V1_CACHE_KEY, None))

        urlopen_mock.return_value = open('test/resources/meta_swagger.json')
        self.app.op
        self.assertIsNotNone(
            self.app.cache.get(self.app.esi_meta_cache_key, None)
        )

    @mock.patch('six.moves.urllib.request.urlopen')
    def test_app_getattr_no_cache(self, urlopen_mock):
        urlopen_mock.return_value = open('test/resources/meta_swagger.json')
        app_nocache = EsiApp(cache=None, cache_prefix=self.ESI_CACHE_PREFIX)

        urlopen_mock.return_value = open('test/resources/swagger.json')
        self.assertIsNone(
            app_nocache.cache.get(self.app.esi_meta_cache_key, None)
        )
        appv1 = app_nocache.get_v1_swagger

        self.assertTrue(isinstance(appv1, App))
        self.assertIsNone(app_nocache.cache.get(self.ESI_V1_CACHE_KEY, None))
