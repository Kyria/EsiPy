# -*- encoding: utf-8 -*-
# pylint: skip-file
from __future__ import absolute_import

import logging
import time
import unittest
import warnings
import json

from requests.utils import quote
from jose.exceptions import JWTError
import six
import httmock

from esipy import EsiSecurity
from esipy.events import Signal
from esipy.exceptions import APIException

from .mock import _all_auth_mock_
from .mock import non_json_error
from .mock import oauth_token
from .mock import oauth_revoke

# set pyswagger logger to error, as it displays too much thing for test needs
pyswagger_logger = logging.getLogger('pyswagger')
pyswagger_logger.setLevel(logging.ERROR)


class TestEsiSecurity(unittest.TestCase):
    CALLBACK_URI = "https://foo.bar/baz/callback"
    CLIENT_ID = 'foo'
    SECRET_KEY = 'bar'
    BASIC_TOKEN = six.u('Zm9vOmJhcg==')
    SECURITY_NAME = 'evesso'
    TOKEN_IDENTIFIER = 'ESIPY_TEST_TOKEN'
    CODE_VERIFIER = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    CODE_CHALLENGE = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"

    RSC_SSO_ENDPOINTS = "test/resources/oauth-authorization-server.json"
    RSC_JWKS = "test/resources/jwks.json"

    def setUp(self):
        warnings.simplefilter('ignore')
        self.custom_refresh_token_signal = Signal()

        with httmock.HTTMock(*_all_auth_mock_):
            self.security = EsiSecurity(
                redirect_uri=TestEsiSecurity.CALLBACK_URI,
                client_id=TestEsiSecurity.CLIENT_ID,
                secret_key=TestEsiSecurity.SECRET_KEY,
                signal_token_updated=self.custom_refresh_token_signal,
                token_identifier=TestEsiSecurity.TOKEN_IDENTIFIER
            )
            self.security_pkce = EsiSecurity(
                redirect_uri=TestEsiSecurity.CALLBACK_URI,
                client_id=TestEsiSecurity.CLIENT_ID,
                code_verifier=TestEsiSecurity.CODE_VERIFIER,
            )

        with open(TestEsiSecurity.RSC_SSO_ENDPOINTS, 'r') as sso_endpoints:
            self.sso_endpoints = json.load(sso_endpoints)

    def test_esisecurity_init(self):
        with httmock.HTTMock(*_all_auth_mock_):
            with self.assertRaises(AttributeError):
                EsiSecurity(
                    redirect_uri=TestEsiSecurity.CALLBACK_URI,
                    client_id=TestEsiSecurity.CLIENT_ID,
                    secret_key=TestEsiSecurity.SECRET_KEY,
                    sso_endpoints_url=""
                )

            with self.assertRaises(AttributeError):
                EsiSecurity(
                    redirect_uri=TestEsiSecurity.CALLBACK_URI,
                    client_id=TestEsiSecurity.CLIENT_ID
                )

            with open(TestEsiSecurity.RSC_JWKS, 'r') as jwks:
                jwks = json.load(jwks)
                EsiSecurity(
                    redirect_uri=TestEsiSecurity.CALLBACK_URI,
                    client_id=TestEsiSecurity.CLIENT_ID,
                    secret_key=TestEsiSecurity.SECRET_KEY,
                    jwks_key=jwks['keys'][0]
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
            self.security.token_identifier,
            TestEsiSecurity.TOKEN_IDENTIFIER
        )
        self.assertEqual(
            self.security.oauth_issuer,
            self.sso_endpoints['issuer']
        )
        self.assertEqual(
            self.security.oauth_authorize,
            self.sso_endpoints['authorization_endpoint']
        )
        self.assertEqual(
            self.security.oauth_token,
            self.sso_endpoints['token_endpoint']
        )
        self.assertEqual(
            self.security.oauth_revoke,
            self.sso_endpoints['revocation_endpoint']
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
        with self.assertRaises(AttributeError):
            self.security.get_auth_uri(state="")

        self.assertEqual(
            self.security.get_auth_uri(state='teststate'),
            ("%s?response_type=code"
             "&redirect_uri=%s&client_id=%s&state=teststate") % (
                self.sso_endpoints['authorization_endpoint'],
                quote(TestEsiSecurity.CALLBACK_URI, safe=''),
                TestEsiSecurity.CLIENT_ID
            )
        )

        self.assertEqual(
            self.security.get_auth_uri(implicit=True, state='teststate'),
            ("%s?response_type=token"
             "&redirect_uri=%s&client_id=%s&state=teststate") % (
                self.sso_endpoints['authorization_endpoint'],
                quote(TestEsiSecurity.CALLBACK_URI, safe=''),
                TestEsiSecurity.CLIENT_ID
            )
        )

        scopes = ["Scope1", "Scope2"]
        self.assertEqual(
            self.security.get_auth_uri(scopes=scopes, state='teststate'),
            ("%s?response_type=code&redirect_uri=%s"
             "&client_id=%s&scope=Scope1+Scope2&state=teststate") % (
                self.sso_endpoints['authorization_endpoint'],
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
            self.sso_endpoints['token_endpoint']
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

        # refresh all scopes
        params = self.security.get_refresh_token_params()
        self.assertEqual(
            params['headers'],
            {'Authorization': 'Basic %s' % TestEsiSecurity.BASIC_TOKEN}
        )
        self.assertEqual(
            params['url'],
            self.sso_endpoints['token_endpoint']
        )
        self.assertEqual(
            params['data'],
            {
                'grant_type': 'refresh_token',
                'refresh_token': 'refresh_token',
            }
        )

        # refresh specific scopes
        params = self.security.get_refresh_token_params(scope_list=['a', 'b'])
        self.assertEqual(
            params['data'],
            {
                'grant_type': 'refresh_token',
                'refresh_token': 'refresh_token',
                'scope': 'a+b'
            }
        )

        # refresh specific scopes exception
        with self.assertRaises(AttributeError):
            self.security.get_refresh_token_params(scope_list='notalist')

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
        # this is just for coverage purpose. This doesn't work without valid
        # jwt token
        with self.assertRaises(AttributeError):
            self.security.verify()

        self.security.update_token({
            'access_token': 'access_token',
            'refresh_token': 'refresh_token',
            'expires_in': 60
        })
        with self.assertRaises(JWTError):
            self.security.verify()
        with httmock.HTTMock(*_all_auth_mock_):
            with open(TestEsiSecurity.RSC_JWKS, 'r') as jwks:
                jwks = json.load(jwks)
                security_nojwks = EsiSecurity(
                    redirect_uri=TestEsiSecurity.CALLBACK_URI,
                    client_id=TestEsiSecurity.CLIENT_ID,
                    secret_key=TestEsiSecurity.SECRET_KEY,
                    jwks_key=jwks['keys'][0]
                )

        security_nojwks.update_token({
            'access_token': 'access_token',
            'refresh_token': 'refresh_token',
            'expires_in': 60
        })
        with self.assertRaises(JWTError):
            security_nojwks.verify()

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
            """ pyswagger Request object over simplified for test purpose"""
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

    def test_esisecurity_pkce(self):
        uri = self.security_pkce.get_auth_uri('test')
        self.assertIn(
            'code_challenge=%s' % TestEsiSecurity.CODE_CHALLENGE,
            uri
        )

        params = self.security_pkce.get_access_token_params('test')
        self.assertEqual(
            params['data']['code_verifier'],
            TestEsiSecurity.CODE_VERIFIER
        )
        self.assertEqual(
            params['data']['client_id'],
            TestEsiSecurity.CLIENT_ID
        )
        self.assertNotIn('Authorization', params['headers'])
