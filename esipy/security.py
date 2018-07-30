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
from six.moves.urllib.parse import urlparse

from .events import AFTER_TOKEN_REFRESH
from .exceptions import APIException

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
            secret_key,
            **kwargs):
        """ Init the ESI Security Object

        :param redirect_uri: the uri to redirect the user after login into SSO
        :param client_id: the OAuth2 client ID
        :param secret_key: the OAuth2 secret key
        :param sso_url: the default sso URL used when no "app" is provided
        :param esi_url: the default esi URL used for verify endpoint
        :param app: (optionnal) the pyswagger app object
        :param token_identifier: (optional) identifies the token for the user
            the value will then be passed as argument to any callback
        :param security_name: (optionnal) the name of the object holding the
            informations in the securityDefinitions,
            used to check authed endpoint
        :param esi_datasource: (optional) The ESI datasource used to validate
            SSO authentication. Defaults to tranquility
        :param headers: (optional) additional headers to add to the requests
            done here
        :param signal_token_updated: (optional) allow to define a specific
            signal to use, instead of using the global AFTER_TOKEN_REFRESH
        """
        app = kwargs.pop('app', None)
        sso_url = kwargs.pop('sso_url', "https://login.eveonline.com")
        esi_url = kwargs.pop('esi_url', "https://esi.evetech.net")
        esi_datasource = kwargs.pop('esi_datasource', "tranquility")

        self.security_name = kwargs.pop('security_name', 'evesso')
        self.redirect_uri = redirect_uri
        self.client_id = client_id
        self.secret_key = secret_key
        self.token_identifier = kwargs.pop('token_identifier', None)

        # we provide app object, so we don't use sso_url
        if app is not None:
            # check if the security_name exists in the securityDefinition
            security = app.root.securityDefinitions.get(
                self.security_name,
                None
            )
            if security is None:
                raise NameError(
                    "%s is not defined in the securityDefinitions" %
                    self.security_name
                )

            self.oauth_authorize = security.authorizationUrl

            # some URL we still need to "manually" define... sadly
            # we parse the authUrl so we don't care if it's TQ or SISI.
            # https://github.com/ccpgames/esi-issues/issues/92
            parsed_uri = urlparse(security.authorizationUrl)
            self.oauth_token = '%s://%s/oauth/token' % (
                parsed_uri.scheme,
                parsed_uri.netloc
            )
            self.oauth_revoke = '%s://%s/oauth/revoke' % (
                parsed_uri.scheme,
                parsed_uri.netloc
            )

        # no app object is provided, so we use direct URLs
        else:
            if sso_url is None or sso_url == "":
                raise AttributeError("sso_url cannot be None or empty "
                                     "without app parameter")

            self.oauth_authorize = '%s/oauth/authorize' % sso_url
            self.oauth_token = '%s/oauth/token' % sso_url
            self.oauth_revoke = '%s/oauth/revoke' % sso_url

        # use ESI url for verify, since it's better for caching
        if esi_url is None or esi_url == "":
            raise AttributeError("esi_url cannot be None or empty")
        self.oauth_verify = '%s/verify/?datasource=%s' % (
            esi_url,
            esi_datasource
        )

        # session request stuff
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

        # token data
        self.refresh_token = None
        self.access_token = None
        self.token_expiry = None

        # other stuff
        self.signal_token_updated = kwargs.pop(
            'signal_token_updated',
            AFTER_TOKEN_REFRESH
        )

    def __get_token_auth_header(self):
        """ Return the Basic Authorization header required to get the tokens

        :return: a dict with the headers
        """
        # encode/decode for py2/py3 compatibility
        auth_b64 = "%s:%s" % (self.client_id, self.secret_key)
        auth_b64 = base64.b64encode(auth_b64.encode('latin-1'))
        auth_b64 = auth_b64.decode('latin-1')

        return {'Authorization': 'Basic %s' % auth_b64}

    def __get_oauth_header(self):
        """ Return the Bearer Authorization header required in oauth calls

        :return: a dict with the authorization header
        """
        return {'Authorization': 'Bearer %s' % self.access_token}

    def __make_token_request_parameters(self, params):
        """ Return the token uri from the securityDefinition

        :param params: the data given to the request
        :return: the oauth/token uri
        """
        request_params = {
            'headers': self.__get_token_auth_header(),
            'data': params,
            'url': self.oauth_token,
        }

        return request_params

    def get_auth_uri(self, scopes=None, state=None, implicit=False):
        """ Constructs the full auth uri and returns it.

        :param scopes: The list of scope
        :param state: The state to pass through the auth process
        :return: the authorizationUrl with the correct parameters.
        """
        scopes_list = [] if not scopes else scopes

        response_type = 'code' if not implicit else 'token'

        return '%s?response_type=%s&redirect_uri=%s&client_id=%s%s%s' % (
            self.oauth_authorize,
            response_type,
            quote(self.redirect_uri, safe=''),
            self.client_id,
            '&scope=%s' % '+'.join(scopes_list) if scopes else '',
            '&state=%s' % state if state else ''
        )

    def get_access_token_params(self, code):
        """ Return the param object for the post() call to get the access_token
        from the auth process (using the code)

        :param code: the code get from the authentification process
        :return: a dict with the url, params and header
        """
        return self.__make_token_request_parameters(
            {
                'grant_type': 'authorization_code',
                'code': code,
            }
        )

    def get_refresh_token_params(self):
        """ Return the param object for the post() call to get the access_token
        from the refresh_token

        :param code: the refresh token
        :return: a dict with the url, params and header
        """
        if self.refresh_token is None:
            raise AttributeError('No refresh token is defined.')

        return self.__make_token_request_parameters(
            {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
            }
        )

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

    def refresh(self):
        """ Update the auth data (tokens) using the refresh token in auth.
        """
        request_data = self.get_refresh_token_params()
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
        """ Revoke the current tokens then empty all stored tokens
        This returns nothing since the endpoint return HTTP/200
        whatever the result is... """
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

        request_data = {
            'headers': self.__get_token_auth_header(),
            'data': data,
            'url': self.oauth_revoke,
        }

        self._session.post(**request_data)
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None

    def verify(self):
        """ Make a get call to the oauth/verify endpoint to get the user data

        :return: the json with the data.
        """
        res = self._session.get(
            self.oauth_verify,
            headers=self.__get_oauth_header()
        )
        if res.status_code != 200:
            raise APIException(
                self.oauth_verify,
                res.status_code,
                response=res.content,
                request_param=self.__get_oauth_header(),
                response_header=res.headers
            )
        return res.json()

    def __call__(self, request):
        """ Check if the request need security header and apply them.
        Required for pyswagger.core.BaseClient.request().

        :param request: the pyswagger request object to check
        :return: the updated request.
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
                request._p['header'].update(self.__get_oauth_header())

        return request
