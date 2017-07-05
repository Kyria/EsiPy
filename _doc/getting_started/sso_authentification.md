---
layout: base
section: getting_started/sso_authentification
title: EVE SSO Authentification
---
# Using EsiPy with EVE SSO

As soon as you want to start using authed endpoints with ESI, you'll have to deal with the EVE SSO. This is what the `EsiSecurity` object is made for.

## developers.eveonline.com

First thing first, you'll have to create an application on [https://developers.eveonline.com/](https://developers.eveonline.com/) to get:
* your `Client ID`
* your `Secret Key`
* your `Callback URL`
* the scopes you want to use.

Once you have all this, lets continue.

## EsiSecurity

The `EsiSecurity` object provides:
* Helper functions to manage SSO (Auth URL, tokens management)
* Headers autofilling when doing requests to add OAuth2 headers
* Tokens management (get, refresh)

```python
from esipy import 

# creating the security object
security = EsiSecurity(
    app=app,
    redirect_uri='https://callback.com/you/set/on/developers/eveonline',
    client_id='you client id',
    secret_key='the_secret_key',
)

# when you have a security object, you need to give it to the client
# so he knows where to get auth headers for authed endpoints.
# --> simplified client
client = EsiClient(security=security)
```

<br><br>

## EVE SSO Authentification

To authenticate yourself to the EVE SSO, you'll need to follow the auth flow from [Eve Third Party Documentation](http://eveonline-third-party-documentation.readthedocs.io/en/latest/sso/authentication.html).

We'll see here `EsiSecurity` methods that allow you to follow this auth flow.

<span class="alert alert-dismissible alert-info">
	<strong>Reminder:</strong> This is only a basic set of information. <br>
	If you want to see a full example with login, see the examples in the menu, or go to <a href="/EsiPy/examples/sso_login_esipy/">this page</a>
</span>

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

