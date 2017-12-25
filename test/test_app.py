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

    @mock.patch('six.moves.urllib.request.urlopen')
    def setUp(self, urlopen_mock):
        # I hate those mock... thx urlopen instead of requests...
        urlopen_mock.return_value = open('test/resources/meta_swagger.json')
        self.app = EsiApp(cache_time=None)

    def test_app_op_attribute(self):
        self.assertTrue(self.app.op)
        self.assertEqual(
            self.app.op['verify'].url,
            '//esi.tech.ccp.is/verify/'
        )

    def test_app_getattr_fail(self):
        with self.assertRaises(AttributeError):
            self.app.doesnotexist

        with self.assertRaises(AttributeError):
            self.app.verify

    @mock.patch('six.moves.urllib.request.urlopen')
    def test_app_getattr_and_cache(self, urlopen_mock):
        urlopen_mock.return_value = open('test/resources/swagger.json')
        self.assertFalse(self.app.cached_version)
        appv1 = self.app.get_v1_swagger

        self.assertTrue(isinstance(appv1, App))
        self.assertEqual(
            self.app.cached_version[0],
            'https://esi.tech.ccp.is/v1/swagger.json'
        )
        self.assertEqual(
            self.app.cache.get('https://esi.tech.ccp.is/v1/swagger.json'),
            appv1
        )

        urlopen_mock.return_value = open('test/resources/meta_swagger.json')
        appv1_bis = self.app.get_v1_swagger
        self.assertEqual(appv1, appv1_bis)

        urlopen_mock.return_value = open('test/resources/meta_swagger.json')
        self.app.force_update()
        self.assertFalse(self.app.cached_version)
        self.assertEqual(
            self.app.cache.get(
                'https://esi.tech.ccp.is/v1/swagger.json',
                None
            ),
            None
        )

    @mock.patch('six.moves.urllib.request.urlopen')
    def test_app_getattr_no_cache(self, urlopen_mock):
        urlopen_mock.return_value = open('test/resources/meta_swagger.json')
        app_nocache = EsiApp(cache=None)

        urlopen_mock.return_value = open('test/resources/swagger.json')
        self.assertFalse(app_nocache.cached_version)
        appv1 = app_nocache.get_v1_swagger

        self.assertTrue(isinstance(appv1, App))
        self.assertFalse(app_nocache.cached_version)
        self.assertEqual(
            app_nocache.cache.get(
                'https://esi.tech.ccp.is/v1/swagger.json',
                None
            ),
            None
        )
