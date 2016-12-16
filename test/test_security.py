# -*- encoding: utf-8 -*-
from __future__ import absolute_import

from .mock import oauth_token
from .mock import oauth_verify
from .mock import oauth_verify_fail
from esipy import App
from esipy import EsiSecurity
from esipy.exceptions import APIException

from requests.utils import quote

import httmock
import mock
import six
import time
import unittest

import logging
# set pyswagger logger to error, as it displays too much thing for test needs
pyswagger_logger = logging.getLogger('pyswagger')
pyswagger_logger.setLevel(logging.ERROR)


class TestEsiSecurity(unittest.TestCase):
    CALLBACK_URI = "https://foo.bar/baz/callback"
    LOGIN_EVE = "https://login.eveonline.com"
    OAUTH_VERIFY = "%s/oauth/verify" % LOGIN_EVE
    OAUTH_TOKEN = "%s/oauth/token" % LOGIN_EVE
    CLIENT_ID = 'foo'
    SECRET_KEY = 'bar'
    BASIC_TOKEN = six.u('Zm9vOmJhcg==')
    SECURITY_NAME = 'evesso'

    @mock.patch('six.moves.urllib.request.urlopen')
    def setUp(self, urlopen_mock):
        # I hate those mock... thx urlopen instead of requests...
        urlopen_mock.return_value = open('test/resources/swagger.json')

        self.app = App.create(
            'https://esi.tech.ccp.is/latest/swagger.json'
        )

        self.security = EsiSecurity(
            self.app,
            TestEsiSecurity.CALLBACK_URI,
            TestEsiSecurity.CLIENT_ID,
            TestEsiSecurity.SECRET_KEY
        )

    def test_esisecurity_init(self):
        with self.assertRaises(NameError):
            EsiSecurity(
                self.app,
                TestEsiSecurity.CALLBACK_URI,
                TestEsiSecurity.CLIENT_ID,
                TestEsiSecurity.SECRET_KEY,
                "security_name_that_does_not_exist"
            )

        self.assertEqual(
            self.security.security_name,
            TestEsiSecurity.SECURITY_NAME
        )
        self.assertEqual(
            self.security.redirect_uri,
            TestEsiSecurity.CALLBACK_URI
        )
        self.assertEqual(
            self.security.client_id,
            TestEsiSecurity.CLIENT_ID
        )
        self.assertEqual(
            self.security.secret_key,
            TestEsiSecurity.SECRET_KEY
        )
        self.assertEqual(
            self.security.oauth_verify,
            TestEsiSecurity.OAUTH_VERIFY
        )
        self.assertEqual(
            self.security.oauth_token,
            TestEsiSecurity.OAUTH_TOKEN
        )

    def test_esisecurity_update_token(self):
        self.security.update_token({
            'access_token': 'access_token',
            'refresh_token': 'refresh_token',
            'expires_in': 60
        })
        self.assertEqual(self.security.access_token, 'access_token')
        self.assertEqual(self.security.refresh_token, 'refresh_token')
        self.assertEqual(self.security.token_expiry, int(time.time()+60))

    def test_esisecurity_get_auth_uri(self):
        self.assertEqual(
            self.security.get_auth_uri(),
            ("%s/oauth/authorize?response_type=code"
             "&redirect_uri=%s&client_id=%s") % (
                TestEsiSecurity.LOGIN_EVE,
                quote(TestEsiSecurity.CALLBACK_URI, safe=''),
                TestEsiSecurity.CLIENT_ID
            )
        )

        self.assertEqual(
            self.security.get_auth_uri(implicit=True),
            ("%s/oauth/authorize?response_type=token"
             "&redirect_uri=%s&client_id=%s") % (
                TestEsiSecurity.LOGIN_EVE,
                quote(TestEsiSecurity.CALLBACK_URI, safe=''),
                TestEsiSecurity.CLIENT_ID
            )
        )

        scopes = ["Scope1", "Scope2"]
        state = "foo"
        self.assertEqual(
            self.security.get_auth_uri(scopes, state),
            ("%s/oauth/authorize?response_type=code&redirect_uri=%s"
             "&client_id=%s&scope=Scope1+Scope2&state=foo") % (
                TestEsiSecurity.LOGIN_EVE,
                quote(TestEsiSecurity.CALLBACK_URI, safe=''),
                TestEsiSecurity.CLIENT_ID
            )
        )

    def test_esisecurity_get_access_token_request_params(self):
        params = self.security.get_access_token_request_params('foo')
        self.assertEqual(
            params['headers'],
            {'Authorization': 'Basic %s' % TestEsiSecurity.BASIC_TOKEN}
        )
        self.assertEqual(
            params['url'],
            TestEsiSecurity.OAUTH_TOKEN
        )
        self.assertEqual(
            params['data'],
            {
                'grant_type': 'authorization_code',
                'code': 'foo',
            }
        )

    def test_esisecurity_get_refresh_token_request_params(self):
        with self.assertRaises(AttributeError):
            self.security.get_refresh_token_request_params()

        self.security.update_token({
            'access_token': 'access_token',
            'refresh_token': 'refresh_token',
            'expires_in': 60
        })

        params = self.security.get_refresh_token_request_params()

        self.assertEqual(
            params['headers'],
            {'Authorization': 'Basic %s' % TestEsiSecurity.BASIC_TOKEN}
        )
        self.assertEqual(
            params['url'],
            TestEsiSecurity.OAUTH_TOKEN
        )
        self.assertEqual(
            params['data'],
            {
                'grant_type': 'refresh_token',
                'refresh_token': 'refresh_token',
            }
        )

    def test_esisecurity_token_expiry(self):
        self.security.token_expiry = None
        self.assertTrue(self.security.is_token_expired())

        self.security.token_expiry = time.time() - 10
        self.assertTrue(self.security.is_token_expired())

        self.security.token_expiry = time.time() + 60
        self.assertFalse(self.security.is_token_expired())
        self.assertTrue(self.security.is_token_expired(offset=70))

    def test_esisecurity_auth(self):
        with httmock.HTTMock(oauth_token):
            ret = self.security.auth('let it bee')
            self.assertEqual(ret['access_token'], 'access_token')
            self.assertEqual(ret['refresh_token'], 'refresh_token')
            self.assertEqual(ret['expires_in'], 1200)

            ret = self.security.auth('no_refresh')
            self.assertEqual(ret['access_token'], 'access_token')
            self.assertNotIn('refresh_token', ret)
            self.assertEqual(ret['expires_in'], 1200)

            with self.assertRaises(APIException):
                self.security.auth('fail_test')

    def test_esisecurity_refresh(self):
        with httmock.HTTMock(oauth_token):
            self.security.refresh_token = 'refresh_token'
            ret = self.security.refresh()
            self.assertEqual(ret['access_token'], 'access_token')
            self.assertEqual(ret['refresh_token'], 'refresh_token')
            self.assertEqual(ret['expires_in'], 1200)

            with self.assertRaises(APIException):
                self.security.refresh_token = 'fail_test_token'
                self.security.refresh()

    def test_esisecurity_verify(self):
        self.security.update_token({
            'access_token': 'access_token',
            'refresh_token': 'refresh_token',
            'expires_in': 60
        })

        with httmock.HTTMock(oauth_verify):
            char_data = self.security.verify()
            self.assertEqual(char_data['CharacterID'], 123456789)
            self.assertEqual(char_data['CharacterName'], 'EsiPy Tester')
            self.assertEqual(char_data['CharacterOwnerHash'], 'YetAnotherHash')

        with httmock.HTTMock(oauth_verify_fail):
            with self.assertRaises(APIException):
                self.security.verify()

    def test_esisecurity_call(self):
        class RequestTest(object):
            def __init__(self):
                self._security = []
                self._p = {'header': {}}

        self.security.update_token({
            'access_token': 'access_token',
            'refresh_token': 'refresh_token',
            'expires_in': 60
        })

        req = RequestTest()
        self.security(req)
        self.assertNotIn('Authorization', req._p['header'])

        req._security.append({
            'unknown_security_name': {},
        })
        self.security(req)
        self.assertNotIn('Authorization', req._p['header'])

        req._security.append({
            'evesso': {},
        })
        self.security(req)
        self.assertIn('Authorization', req._p['header'])
        self.assertEqual(
            'Bearer access_token',
            req._p['header']['Authorization']
        )
