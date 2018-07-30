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
* **secret_key** - the OAuth2 secret key
* **headers** - A dict containing any header you want to add. Not adding `User-Agent` header will trigger a warn.
* **sso_url** - The default sso URL used when no "app" is provided. Default is `https://login.eveonline.com`
* **esi_url** - The default esi URL used for verify endpoint. Default is `https://esi.evetech.net`
* **app** - The pyswagger app object. This will be used in place of sso_url.
* **token_identifier** - Identifies the token for the user the value will then be passed as argument to any callback
* **security_name** - The name of the object holding the informations in the securityDefinitions, used to check authed endpoint. Default is `evesso`
* **esi_datasource** - The ESI datasource used to validate SSO authentication. Defaults to `tranquility`
* **signal_token_updated** - Allow to define a custom Signal to replace `AFTER_TOKEN_REFRESH` using `signal_token_updated` when initializing the client

### `EsiSecurity.verify()`
Make a call to the verify endpoint with the current tokens and return the json data.

### `EsiSecurity.auth(code)`
Get the tokens from SSO using the given code, and return the json response containing the tokens.²²

**Parameters:**
* **code** - The code sent by EVE SSO when the logger

### `EsiSecurity.refresh()`
Use the given refresh token (using `update_token` or `auth`) to get a new access_token.

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

### `EsiSecurity.get_auth_uri(scopes=None, state=None, implicit=False)`
Generate the SSO auth URL, using the given parameters and `EsiSecurity` attributes.

**Parameters:** All parameters are optional.
* **scopes** - The list of scopes to add to the auth URL
* **state** - The state to add to the URL
* **implicit** - Generate the URL for a implicit flow auth.
