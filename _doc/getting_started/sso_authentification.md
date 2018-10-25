---
layout: base
section: getting_started/sso_authentification
title: EVE SSO Authentification
---
# Using EsiPy with EVE SSO

As soon as you want to start using authed endpoints with ESI, you'll have to deal with the EVE SSO. This is what the `EsiSecurity` object is made for.

&nbsp;

## developers.eveonline.com

First thing first, you'll have to create an application on [https://developers.eveonline.com/](https://developers.eveonline.com/) to get:
* your `Client ID`
* your `Secret Key`
* your `Callback URL`
* the scopes you want to use.

Once you have all this, lets continue.

&nbsp;

## EsiSecurity

The `EsiSecurity` object provides:
* Helper functions to manage SSO (Auth URL, tokens management)
* Headers autofilling when doing requests to add OAuth2 headers
* Tokens management (get, refresh)

#### ClientID / Secret Key

`EsiSecurity.__init__()` takes at least the following parameters with clientID / Secret Key. 

Parameter | Type | Description
--- | --- | ---
redirect_uri | String | The URI you want the user redirected after he logs in with EVE SSO
client_id | String | You client ID from developers.eveonline.com
secret_key | String | You secret key from developers.eveonline.com

<div class="alert alert-dismissible alert-info">
    For more details about EsiApp, please see <a href="/EsiPy/api/esisecurity/">this page</a>.
</div>

```python
from esipy import EsiSecurity

# creating the security object using the app
security = EsiSecurity(
    redirect_uri='https://callback.com/you/set/on/developers/eveonline',
    client_id='you client id',
    secret_key='the_secret_key',
)

# when you have a security object, you need to give it to the client
# so he knows where to get auth headers for authed endpoints.
# --> simplified client
client = EsiClient(security=security)
```

#### PKCE

You can also use the security object to use the PKCE flow (especially for desktop application without secret key). <br>
All you need is to replace the `secret_key` parameter with `code_verifier`.

Parameter | Type | Description
--- | --- | ---
redirect_uri | String | The URI you want the user redirected after he logs in with EVE SSO
client_id | String | You client ID from developers.eveonline.com
code_verifier | String | A code used for the PKCE flow. Must follow RFC 7636

If you don't know how to generate a random `code_verifier` you can use the [`esipy.utils.generate_code_verifier()`](https://github.com/Kyria/EsiPy/blob/master/esipy/utils.py#L48) function.<br>
**`EsiSecurity` will only use PKCE flow if `secret_key` is not given / is None. In any other case, it won't be used**

Once you have created the `EsiSecurity` object with the `code_verifier`, you can use it like you would in other cases. 

```python
from esipy import EsiSecurity
from esipy.utils import generate_code_verifier

# creating the security object using the app
security = EsiSecurity(
    redirect_uri='https://callback.com/you/set/on/developers/eveonline',
    client_id='you client id',
    code_verifier=generate_code_verifier(),
)

client = EsiClient(security=security)
```

&nbsp;

## EVE SSO - Authentification

To authenticate yourself to the EVE SSO, you'll need to follow the OAuth auth flow. You can find more informations about it in [ESI Documentation](https://docs.esi.evetech.net/docs/sso/#table-of-contents).

We'll see here `EsiSecurity` methods that allow you to follow this auth flow.

<div class="alert alert-dismissible alert-info">
	<strong>Reminder:</strong> This is only a basic set of information. <br>
	If you want to see a full example with login, see the examples in the menu, or go to <a href="/EsiPy/examples/sso_login_esipy/">this page</a>
</div>

#### Redirecting the user to EVE SSO Login

First, you'll need to make your user go the SSO Login from EVE Online.

As the login URL have to have some mandatory informations in it, you can use the `EsiSecurity.get_auth_uri()` method:

```python
# this will give you the url where your user must be redirected to.
eve_sso_auth_url = security.get_auth_uri(
	scopes=['Scope1', 'Scope2', 'Scope3'],  # or None (default) if you don't need any scope
	state="what you want and can be None(default)"
)
```

#### Code from login

Once your user logged in, he will be redirected to your callback URL, with a `code` parameter.

With that code, you can tell the security object to get the token.

```python
# this returns
tokens = esi_security.auth(code_you_get_from_user_login)

# tokens is actually a json objects with these values:
# {
#     "access_token":"uNEEh...a_WpiaA2",
#     "token_type":"Bearer",
#     "expires_in":1200,
#     "refresh_token":"gEy...fM0"
# }
```

Now the security object knows everything, it can use OAuth endpoints without problems. <br>
You don't also have to get the tokens returned if you don't need them as they are stored within the security object.

#### Getting the logged in character informations

When you are logged in, you can get the character data with the verify method.

```python
esi_security.verify()

# returns this json object:
{
    "CharacterID": 123456487,
    "CharacterName": "Char Name",
    "ExpiresOn": "2016-12-23T15:26:46.555002",
    "Scopes": "publicData",
    "TokenType": "Character",
    "CharacterOwnerHash": "aef564ae6fae46era4fer8=",
    "IntellectualProperty": "EVE"
}
```

&nbsp;

## EVE SSO - Revoking tokens

In case you want or need to revoke tokens, you can do it by simply calling the `EsiSecurity.revoke()` method.
Make sure you first updated your security object with the token, else you'll get an error!

```python

# This doesn't have to be done if you just logged in with "auth()" or "refresh()"
# here for the example we only set "refresh_token", but it'd work with only "access_token"
security.update_token({
    'access_token': ''
    'expires_in': -1,  # seconds until expiry, so we force refresh anyway
    'refresh_token': 'YOUR_SAVED_REFRESH_TOKEN'
})

# this doesn't return anything, as EVE SSO doesn't
security.revoke()

# and you are done.
```

If you call this `revoke()` multiple time without updating the tokens, you will get an Exception `AttributeError: No access/refresh token are defined.`, as they are removed from the security object at the end of the process.
