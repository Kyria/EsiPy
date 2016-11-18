# -*- encoding: utf-8 -*-
from requests.utils import quote
import six


class EsiSecurity(object):
    """ Contains all the OAuth2 knowledge for ESI use.
    Based on pyswagger Security object, to be used with pyswagger BaseClient
    implementation.
    """

    def __init__(
            self,
            app,
            redirect_uri,
            client_id,
            secret_key,
            security_name="evesso"):
        """ Init the ESI Security Object

        :param app: the pyswagger app object
        :param redirect_uri: the uri to redirect the user after login into SSO
        :param client_id: the OAuth2 client ID
        :param secret_key: the OAuth2 secret key
        :param security_name: (optionnal) the name of the object holding the
        informations in the securityDefinitions.

        """
        # check if the security_name actually exists in the securityDefinition
        if app.root.securityDefinitions.get(security_name, None) is None:
            raise NameError(
                "%s is not defined in the securityDefinitions" % security_name
            )

        self.app = app
        self.security_name = security_name
        self.redirect_uri = redirect_uri
        self.client_id = client_id
        self.secret_key = secret_key

        # token data
        self.refresh_token = None
        self.access_token = None
        self.token_expiry = None

    def get_auth_uri(self, scopes=None, state=None):
        """ Constructs the full auth uri and returns it.

        :param scopes: The list of scope
        :param state: The state to pass through the auth process
        :return: the authorizationUrl with the correct parameters.
        """
        security_definition = self.app.root.securityDefinitions.get(
            self.security_name
        )

        return "%s?response_type=code&redirect_uri=%s&client_id=%s%s%s" % (
            security_definition.authorizationUrl,
            quote(self.redirect_uri, safe=''),
            self.client_id,
            "&scope=%s" % '+'.join(s) if scopes else '',
            "&state=%s" % state if state else ''
        )

    def __make_token_request_parameters(self, params, testing=False):
        """ Return the token uri from the securityDefinition

        :param testing: True if we are on Singularity, else false for TQ.
        :return: the oauth/token uri
        """
        security_definition = self.app.root.securityDefinitions.get(
            self.security_name
        )

        params = {
            'headers': self.get_token_auth_header(),
            'params': params,
        }

        # should be: security_definition.tokenUrl
        # but not yet implemented by CCP in ESI so we need the full URL...
        # https://github.com/ccpgames/esi-issues/issues/92
        if testing:
            params['url'] = "https://sisilogin.testeveonline.com/oauth/token"
        else:
            params['url'] = "https://login.eveonline.com/oauth/token"

        return params

    def get_access_token_request_params(self, code, testing=False):
        """ Return the param object for the post() call to get the access_token
        from the auth process (using the code)

        :param code: the code get from the authentification process
        :param testing: True if we are on Singularity, else false for TQ.
        :return: a dict with the url, params and header
        """
        return self.__make_token_request_parameters(
            {
                "grant_type": "authorization_code",
                "code": code,
            },
            testing
        )

    def get_refresh_token_request_params(self, testing=False):
        """ Return the param object for the post() call to get the access_token
        from the refresh_token

        :param code: the refresh token
        :param testing: True if we are on Singularity, else false for TQ.
        :return: a dict with the url, params and header
        """
        if self.refresh_token is None:
            raise AttributeError('No refresh token is defined.')

        return self.__make_token_request_parameters(
            {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
            testing
        )

    def get_token_auth_header(self):
        """ Return the Basic Authorization header required to get the tokens

        :return: a dict with the headers
        """
        # encode/decode for py2/py3 compatibility
        auth_b64 = "%s:%s" % (self.client_id, self.secret_key)
        auth_b64 = base64.b64encode(auth_b64.encode('latin-1'))
        auth_b64 = auth_b64.decode('latin-1')

        return {"Authorization": "Basic %s" % auth_b64}

    def apply_auth_header(self, request):
        """ Apply the Bearer Authorization header for ESI calls.
        This method is used in the __call__ function.

        :param request: the pyswagger request object where we update the header
        :return: the updated request object
        """
        if self.access_token is not None:
            request._p['header'].update({
                "Authorization": "Bearer %s" % self.access_token
            })
        return request

    def update_token(self, response_json):
        """ Update access_token, refresh_token and token_expiry from the
        response body.
        The response must be converted to a json object before being passed as
        a parameter

        :param response_json: the response body to use.
        """
        self.access_token = response_json['access_token']
        self.token_expiry = int(time.time()) + response_json['expires_in']

        if "refresh_token" in response_json:
            self.refresh_token = response_json['refresh_token']

    def is_token_expired(self, offset=0):
        """ Return true if the token is expired.
        The offset can be used to change the expiry time:
        - positive value decrease the time (sooner)
        - negative value increase the time (later)

        :param offset: the expiry offset (in seconds) [default: 0]
        :return: boolean true if expired, else false.
        """
        return int(time.time()) >= (self.token_expiry - offset)

    def __call__(self, request):
        """ Check if the request need security header and apply them.
        Call by client.request.

        :param request: the pyswagger request object to check
        :return: the updated request.
        """
        if not request._security:
            return request

        for security in request._security:
            if self.security_name not in security:
                logger.warning(
                    'Missing Securities: [%s]' % ', '.join(security.keys())
                )
                continue
            self.apply_auth_header(request)

        return req
