# -*- encoding: utf-8 -*-
""" EsiPy Security definition where everything related to
SSO auth is defined """

from __future__ import absolute_import

import base64
import logging
import time
import warnings

from requests import Session
from requests.utils import quote
from jose import jwt

from .events import AFTER_TOKEN_REFRESH
from .exceptions import APIException
from .utils import generate_code_challenge

LOGGER = logging.getLogger(__name__)


class EsiSecurity(object):
    """ Contains all the OAuth2 knowledge for ESI use.
    Based on pyswagger Security object, to be used with pyswagger BaseClient
    implementation.
    """

    def __init__(
            self,
            redirect_uri,
            client_id,
            secret_key=None,
            code_verifier=None,
            **kwargs):
        """ Init the ESI Security Object

        :param redirect_uri: the uri to redirect the user after login into SSO
        :param client_id: the OAuth2 client ID
        :param secret_key: the OAuth2 secret key
        :param token_identifier: (optional) identifies the token for the user
            the value will then be passed as argument to any callback
        :param security_name: (optionnal) the name of the object holding the
            informations in the securityDefinitions,
            used to check authed endpoint
        :param headers: (optional) additional headers to add to the requests
            done here
        :param signal_token_updated: (optional) allow to define a specific
            signal to use, instead of using the global AFTER_TOKEN_REFRESH
        :param sso_endpoints: (optional)
        :param sso_endpoints_url: (optional)
        :param jwks_key: (optional)
        """
        sso_endpoints_url = kwargs.pop(
            'sso_endpoints_url',
            ('https://login.eveonline.com/'
             '.well-known/oauth-authorization-server')
        )

        if sso_endpoints_url is None or sso_endpoints_url == "":
            raise AttributeError("sso_endpoints_url cannot be None or empty")

        if secret_key is None and code_verifier is None:
            raise AttributeError(
                "Either secret_key or code_verifier must be filled"
            )

        self.security_name = kwargs.pop('security_name', 'evesso')
        self.redirect_uri = redirect_uri
        self.client_id = client_id
        self.secret_key = secret_key
        self.code_verifier = code_verifier

        # session requests stuff
        self._session = Session()
        headers = kwargs.pop('headers', {})
        if 'User-Agent' not in headers:
            warning_message = (
                "Defining a 'User-Agent' header is a"
                " good practice, and allows CCP to contact you if required."
                " To do this, simply add the following when creating"
                " the security object: headers={'User-Agent':'something'}."
            )
            LOGGER.warning(warning_message)
            warnings.warn(warning_message)

            self._session.headers.update({
                'User-Agent': (
                    'EsiPy/Security/ - '
                    'https://github.com/Kyria/EsiPy - '
                    'ClientID: %s' % self.client_id
                )
            })
        self._session.headers.update({"Accept": "application/json"})
        self._session.headers.update(headers)

        # get sso endpoints from given dict, else get it from EVE SSO
        # raise error if not 200 / json fail
        sso_endpoints = kwargs.pop('sso_endpoints', None)
        if sso_endpoints is None or not isinstance(sso_endpoints, dict):
            res = self._session.get(sso_endpoints_url)
            res.raise_for_status()
            sso_endpoints = res.json()

        self.oauth_issuer = sso_endpoints['issuer']
        self.oauth_authorize = sso_endpoints['authorization_endpoint']
        self.oauth_token = sso_endpoints['token_endpoint']
        self.oauth_revoke = sso_endpoints['revocation_endpoint']
        self.__get_jwks_key(sso_endpoints['jwks_uri'], **kwargs)

        # token data
        self.token_identifier = kwargs.pop('token_identifier', None)
        self.refresh_token = None
        self.access_token = None
        self.token_expiry = None

        # other stuff
        self.signal_token_updated = kwargs.pop(
            'signal_token_updated',
            AFTER_TOKEN_REFRESH
        )

    def __get_jwks_key(self, jwks_uri, **kwargs):
        """Get from jwks_ui all the JWK keys required to decode JWT Token.

        Parameters
        ----------
        jwks_uri : string
            The URL where to gather JWKS key
        kwargs : Dict
            The constructor parameters
        """
        jwks_key = kwargs.pop('jwks_key', None)
        if not jwks_key:
            res = self._session.get(jwks_uri)
            res.raise_for_status()
            jwks_key = res.json()

        self.jwks_key_set = None
        self.jwks_key = None
        if 'keys' in jwks_key:
            self.jwks_key_set = {}
            for jwks in jwks_key['keys']:
                self.jwks_key_set[jwks['kid']] = jwks
        else:
            self.jwks_key = jwks_key

    def __get_basic_auth_header(self):
        """Return the Basic Authorization header for oauth if secret_key exists

        Returns
        -------
        type
            A dictionary that contains the Basic Authorization key/value,
            or {} if secret_key is None

        """
        if self.secret_key is None:
            return {}

        # encode/decode for py2/py3 compatibility
        auth_b64 = "%s:%s" % (self.client_id, self.secret_key)
        auth_b64 = base64.b64encode(auth_b64.encode('utf-8'))
        auth_b64 = auth_b64.decode('utf-8')

        return {'Authorization': 'Basic %s' % auth_b64}

    def __prepare_token_request(self, params, url=None):
        """Generate the request parameters to execute the POST call to
        get or refresh a token.

        Parameters
        ----------
        params : dictionary
            Contains the parameters that will be given as data to the oauth
            endpoint

        Returns
        -------
        type
            The filled request parameters with all required informations

        """
        if self.secret_key is None:
            params['code_verifier'] = self.code_verifier
            params['client_id'] = self.client_id

        request_params = {
            'headers': self.__get_basic_auth_header(),
            'data': params,
            'url': self.oauth_token if url is None else url,
        }

        return request_params

    def get_auth_uri(self, state, scopes=None, implicit=False):
        """Constructs the full auth uri and returns it..

        Parameters
        ----------
        state : string
            The state to pass through the auth process
        scopes : list (optional)
            The list of scope to have
        implicit : Boolean (optional)
            Activate or not the implicit flow

        Returns
        -------
        String
            The generated URL for the user to log into EVE SSO

        """
        if state is None or state == '':
            raise AttributeError('"state" must be non empty, non None string')

        scopes_list = [] if not scopes else scopes
        response_type = 'code' if not implicit else 'token'

        # generate the auth URI
        auth_uri = '%s?response_type=%s&redirect_uri=%s&client_id=%s%s%s' % (
            self.oauth_authorize,
            response_type,
            quote(self.redirect_uri, safe=''),
            self.client_id,
            '&scope=%s' % '+'.join(scopes_list) if scopes else '',
            '&state=%s' % state
        )

        # add code challenge if we have one
        if self.secret_key is None and not implicit:
            auth_uri += '&code_challenge_method=S256&code_challenge=%s' % (
                generate_code_challenge(self.code_verifier)
            )
        return auth_uri

    def get_access_token_params(self, code):
        """ Return the param object for the post() call to get the access_token
        from the auth process (using the code)

        :param code: the code get from the authentification process
        :return: a dict with the url, params and header
        """
        params = {
            'grant_type': 'authorization_code',
            'code': code,
        }

        return self.__prepare_token_request(params)

    def get_refresh_token_params(self, scope_list=None):
        """ Return the param object for the post() call to get the access_token
        from the refresh_token

        :param code: the refresh token
        :return: a dict with the url, params and header
        """
        if self.refresh_token is None:
            raise AttributeError('No refresh token is defined.')

        params = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
        }

        if scope_list:
            if isinstance(scope_list, list):
                scopes = '+'.join(scope_list)
            else:
                raise AttributeError('scope_list must be a list of scope.')
            params['scope'] = scopes

        return self.__prepare_token_request(params)

    def update_token(self, response_json, **kwargs):
        """ Update access_token, refresh_token and token_expiry from the
        response body.
        The response must be converted to a json object before being passed as
        a parameter

        :param response_json: the response body to use.
        :param token_identifier: the user identifier for the token
        """
        self.token_identifier = kwargs.pop(
            'token_identifier',
            self.token_identifier
        )
        self.access_token = response_json['access_token']
        self.token_expiry = int(time.time()) + response_json['expires_in']

        if 'refresh_token' in response_json:
            self.refresh_token = response_json['refresh_token']

    def is_token_expired(self, offset=0):
        """ Return true if the token is expired.

        The offset can be used to change the expiry time:
        - positive value decrease the time (sooner)
        - negative value increase the time (later)
        If the expiry is not set, always return True. This case allow the users
        to define a security object, only knowing the refresh_token and get
        a new access_token / expiry_time without errors.

        :param offset: the expiry offset (in seconds) [default: 0]
        :return: boolean true if expired, else false.
        """
        if self.token_expiry is None:
            return True
        return int(time.time()) >= (self.token_expiry - offset)

    def refresh(self, scope_list=None):
        """ Update the auth data (tokens) using the refresh token in auth.
        """
        request_data = self.get_refresh_token_params(scope_list)
        res = self._session.post(**request_data)
        if res.status_code != 200:
            raise APIException(
                request_data['url'],
                res.status_code,
                response=res.content,
                request_param=request_data,
                response_header=res.headers
            )
        json_res = res.json()
        self.update_token(json_res)
        return json_res

    def auth(self, code):
        """ Request the token to the /oauth/token endpoint.
        Update the security tokens.

        :param code: the code you get from the auth process
        """
        request_data = self.get_access_token_params(code)

        res = self._session.post(**request_data)
        if res.status_code != 200:
            raise APIException(
                request_data['url'],
                res.status_code,
                response=res.content,
                request_param=request_data,
                response_header=res.headers
            )

        json_res = res.json()
        self.update_token(json_res)
        return json_res

    def revoke(self):
        """Revoke the current tokens then empty all stored tokens
        This returns nothing since the endpoint return HTTP/200
        whatever the result is...

        Currently not working with JWT, left here for compatibility.
        """
        if not self.refresh_token and not self.access_token:
            raise AttributeError('No access/refresh token are defined.')

        if self.refresh_token:
            data = {
                'token_type_hint': 'refresh_token',
                'token': self.refresh_token,
            }
        else:
            data = {
                'token_type_hint': 'access_token',
                'token': self.access_token,
            }

        request_data = self.__prepare_token_request(data, self.oauth_revoke)

        self._session.post(**request_data)
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None

    def verify(self, kid='JWT-Signature-Key', options=None):
        """Decode and verify the token and return the decoded informations

        Parameters
        ----------
        kid : string
            The JWKS key id to identify the key to decode the token.
            Default is 'JWT-Signature-Key'. Only change if CCP changes it.
        options : Dict
            The dictionary of options for skipping validation steps. See
            https://python-jose.readthedocs.io/en/latest/jwt/api.html#jose.jwt.decode

        Returns
        -------
        Dict
            The JWT informations from the token, such as character name etc.

        Raises
        ------
            jose.exceptions.JWTError: If the signature is invalid in any way.
            jose.exceptions.ExpiredSignatureError: If the signature has expired
            jose.exceptions.JWTClaimsError: If any claim is invalid in any way.
        """
        if self.access_token is None or self.access_token == "":
            raise AttributeError('No access token are available at this time')
        if options is None:
            options = {}

        if self.jwks_key_set is None:
            key = self.jwks_key
        else:
            key = self.jwks_key_set[kid]

        return jwt.decode(
            self.access_token,
            key,
            issuer=self.oauth_issuer,
            options=options
        )

    def __call__(self, request):
        """Check if the request need security header and apply them.
        Required for pyswagger.core.BaseClient.request().

        Parameters
        ----------
        request : pyswagger.io.Request
            the pyswagger request object to check, generated from app operation

        Returns
        -------
        pyswagger.io.Request
            The pyswagger request with auth headers added if required.

        """
        if not request._security:
            return request

        if self.is_token_expired():
            json_response = self.refresh()
            self.signal_token_updated.send(
                token_identifier=self.token_identifier,
                **json_response
            )

        for security in request._security:
            if self.security_name not in security:
                LOGGER.warning(
                    "Missing Securities: [%s]",
                    ", ".join(security.keys())
                )
                continue
            if self.access_token is not None:
                request._p['header'].update(
                    {'Authorization': 'Bearer %s' % self.access_token}
                )

        return request
