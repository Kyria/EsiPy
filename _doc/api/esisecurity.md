---
layout: base
section: api/esisecurity
title: API - EsiSecurity
---
# EsiSecurity

### `EsiSecurity(**kwargs)`
The EsiPy App wrapper that will deal with `pyswagger.App` and caching.

**Parameters:**
* **redirect_uri** - The URL you want to redirect the user after login into SSO
* **client_id** - the OAuth2 client ID
* **secret_key** - *(Optional)* the OAuth2 secret key. Default is `None`. **Either this or code_verifier must be provided**
* **code_verifier** - *(Optional)* the PKCE code verifier Default is `None`. **Either this or secret_key must be provided**
* **headers** - *(Optional)* A dict containing any header you want to add. Not adding `User-Agent` header will trigger a warn.
* **token_identifier** - *(Optional)* Identifies the token for the user the value will then be passed as argument to any callback
* **security_name** - *(Optional)* The name of the object holding the informations in the securityDefinitions, used to check authed endpoint. Default is `evesso`
* **signal_token_updated** - *(Optional)* Allow to define a custom Signal to replace `AFTER_TOKEN_REFRESH` using `signal_token_updated` when initializing the client
* **sso_endpoints_url** - *(Optional)* Discovery URL for SSO endpoints. Default is `https://login.eveonline.com/.well-known/oauth-authorization-server`. Change this URL to use SISI or Serenity SSO.
* **sso_endpoints** - *(Optional)* Dict containing the content of the SSO endpoint discovery URL. Can be used if this information is cached client side. Default is `None`. If this is `None`, `EsiSecurity` will make a request to get the informations.
* **jwks_key** - *(Optional)* Dict containing the content of the SSO JSON Web Key Set (URL found in SSO endpoint discovery). Default is `None`. If this is `None`, `EsiSecurity` will make a request to get the informations.

### `EsiSecurity.verify()`
Use `python-jose` to validate and decode the token and return the token informations.

**Parameters:**
* **kid** - *(Optional)* The key id used to select the key (from the JWKS) to decode and validate the token. Default is `JWT-Signature-Key`.
* **options** - *(Optional)* The dictionary of options for skipping some validation steps. See [this for more details](https://python-jose.readthedocs.io/en/latest/jwt/api.html#jose.jwt.decode)

### `EsiSecurity.auth(code)`
Get the tokens from SSO using the given code, and return the json response containing the tokens.

**Parameters:**
* **code** - The code sent by EVE SSO when the logger

### `EsiSecurity.refresh()`
Use the given refresh token (using `update_token` or `auth`) to get a new access_token.

**Parameters:**
* **scope_list** - *(Optional)* List - Define a subset of scope to refresh. Default is `None`

### `EsiSecurity.revoke()`
Use the current tokens to make a request CCP side to revoke these tokens.

### `EsiSecurity.is_token_expired(offset=0)`
Check if the stored access_token is expired, with the offset `offset`.

**Parameters:**
* **offset** - The number of seconds to offset for the check.

### `EsiSecurity.update_token(response_json, **kwargs)`
Update the security object with the given tokens.

**Parameters:**
* **response_json** - The dict (json) that contains the token information: `{'access_token':'token', 'refresh_token':'token', 'expires_in': seconds`}
* **token_identifier** - The user identifier that identifies the token for him.

### `EsiSecurity.get_auth_uri(state, scopes=None, implicit=False)`
Generate the SSO auth URL, using the given parameters and `EsiSecurity` attributes. If no `secret_key` is provided but `code_verifier`, the function will automatically use the PCKE flow. 

**Parameters:** All parameters are optional.
* **state** - The state to add to the URL
* **scopes** - *(Optional)* The list of scopes to add to the auth URL
* **implicit** - *(Optional)* Generate the URL for a implicit flow auth.
