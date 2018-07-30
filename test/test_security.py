# -*- encoding: utf-8 -*-
# pylint: skip-file
from __future__ import absolute_import

from .mock import non_json_error
from .mock import oauth_token
from .mock import oauth_verify
from .mock import oauth_revoke
from .mock import oauth_verify_fail

from esipy import App
from esipy import EsiSecurity
from esipy.events import Signal
from esipy.exceptions import APIException

from requests.utils import quote

import httmock
import mock
import six
import time
import unittest
import warnings

import logging
# set pyswagger logger to error, as it displays too much thing for test needs
pyswagger_logger = logging.getLogger('pyswagger')
pyswagger_logger.setLevel(logging.ERROR)


class TestEsiSecurity(unittest.TestCase):
    CALLBACK_URI = "https://foo.bar/baz/callback"
    LOGIN_EVE = "https://login.eveonline.com"
    OAUTH_VERIFY = "https://esi.evetech.net/verify/?datasource=tranquility"
    OAUTH_TOKEN = "%s/oauth/token" % LOGIN_EVE
    OAUTH_AUTHORIZE = "%s/oauth/authorize" % LOGIN_EVE
    CLIENT_ID = 'foo'
    SECRET_KEY = 'bar'
    BASIC_TOKEN = six.u('Zm9vOmJhcg==')
    SECURITY_NAME = 'evesso'
    TOKEN_IDENTIFIER = 'ESIPY_TEST_TOKEN'

    @mock.patch('six.moves.urllib.request.urlopen')
    def setUp(self, urlopen_mock):
        # I hate those mock... thx urlopen instead of requests...
        urlopen_mock.return_value = open('test/resources/swagger.json')
        warnings.simplefilter('ignore')

        self.app = App.create(
            'https://esi.evetech.net/latest/swagger.json'
        )

        self.custom_refresh_token_signal = Signal()

        self.security = EsiSecurity(
            app=self.app,
            redirect_uri=TestEsiSecurity.CALLBACK_URI,
            client_id=TestEsiSecurity.CLIENT_ID,
            secret_key=TestEsiSecurity.SECRET_KEY,
            signal_token_updated=self.custom_refresh_token_signal,
            token_identifier=TestEsiSecurity.TOKEN_IDENTIFIER
        )

    def test_esisecurity_init_with_app(self):
        with self.assertRaises(NameError):
            EsiSecurity(
                app=self.app,
                redirect_uri=TestEsiSecurity.CALLBACK_URI,
                client_id=TestEsiSecurity.CLIENT_ID,
                secret_key=TestEsiSecurity.SECRET_KEY,
                security_name="security_name_that_does_not_exist"
            )

        with self.assertRaises(AttributeError):
            EsiSecurity(
                app=self.app,
                redirect_uri=TestEsiSecurity.CALLBACK_URI,
                client_id=TestEsiSecurity.CLIENT_ID,
                secret_key=TestEsiSecurity.SECRET_KEY,
                esi_url=""
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
        self.assertEqual(
            self.security.oauth_authorize,
            TestEsiSecurity.OAUTH_AUTHORIZE
        )
        self.assertEqual(
            self.security.token_identifier,
            TestEsiSecurity.TOKEN_IDENTIFIER
        )

    def test_esisecurity_other_init(self):
        with self.assertRaises(AttributeError):
            EsiSecurity(
                redirect_uri=TestEsiSecurity.CALLBACK_URI,
                client_id=TestEsiSecurity.CLIENT_ID,
                secret_key=TestEsiSecurity.SECRET_KEY,
                sso_url=""
            )

        security = EsiSecurity(
            redirect_uri=TestEsiSecurity.CALLBACK_URI,
            client_id=TestEsiSecurity.CLIENT_ID,
            secret_key=TestEsiSecurity.SECRET_KEY,
            sso_url='foo.com',
            esi_url='bar.baz',
            esi_datasource='singularity'
        )

        self.assertEqual(
            security.oauth_verify,
            "bar.baz/verify/?datasource=singularity"
        )
        self.assertEqual(
            security.oauth_token,
            "foo.com/oauth/token"
        )
        self.assertEqual(
            security.oauth_authorize,
            "foo.com/oauth/authorize"
        )
        self.assertEqual(
            security.token_identifier,
            None
        )

    def test_esisecurity_update_token(self):
        self.security.update_token({
            'access_token': 'access_token',
            'refresh_token': 'refresh_token',
            'expires_in': 60
        })
        self.assertEqual(self.security.access_token, 'access_token')
        self.assertEqual(self.security.refresh_token, 'refresh_token')
        self.assertEqual(self.security.token_expiry, int(time.time() + 60))

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
        params = self.security.get_access_token_params('foo')
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
            self.security.get_refresh_token_params()

        self.security.update_token({
            'access_token': 'access_token',
            'refresh_token': 'refresh_token',
            'expires_in': 60
        })

        params = self.security.get_refresh_token_params()

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

    def test_esisecurity_revoke(self):
        with httmock.HTTMock(oauth_revoke):
            self.security.refresh_token = 'refresh_token'
            self.security.revoke()

            self.security.access_token = 'access_token'
            self.security.revoke()

            with self.assertRaises(AttributeError):
                self.security.revoke()

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

    def test_esisecurity_callback_refresh(self):
        class RequestTest(object):

            def __init__(self):
                self._security = ['evesso']
                self._p = {'header': {}}

        def callback_function(**kwargs):
            callback_function.count += 1
        callback_function.count = 0

        self.custom_refresh_token_signal.add_receiver(callback_function)

        self.security.update_token({
            'access_token': 'access_token',
            'refresh_token': 'refresh_token',
            'expires_in': -1
        })

        # test the auto refresh callback event customized
        with httmock.HTTMock(oauth_token):
            req = RequestTest()
            self.security(req)
            self.assertEqual(callback_function.count, 1)

    def test_esisecurity_non_json_response(self):
        self.security.update_token({
            'access_token': 'access_token',
            'refresh_token': 'refresh_token',
            'expires_in': -1
        })
        with httmock.HTTMock(non_json_error):
            try:
                self.security.verify()
            except APIException as exc:
                self.assertEqual(exc.status_code, 502)
                self.assertEqual(
                    exc.response,
                    six.b('<html><body>Some HTML Errors</body></html>')
                )

            try:
                self.security.auth('somecode')
            except APIException as exc:
                self.assertEqual(exc.status_code, 502)
                self.assertEqual(
                    exc.response,
                    six.b('<html><body>Some HTML Errors</body></html>')
                )

            try:
                self.security.refresh()
            except APIException as exc:
                self.assertEqual(exc.status_code, 502)
                self.assertEqual(
                    exc.response,
                    six.b('<html><body>Some HTML Errors</body></html>')
                )
