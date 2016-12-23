# Authentication

If you want to access endpoints that require some Auth, you'll have to use a EsiSecurity object.

## EsiSecurity

The EsiSecurity provides everything you need that is related to OAuth and SSO for the ESI API.

To work, it will need:
- the App object you created earlier
- a redirect URI
- a client ID
- a secret key
- a security name (this is defined in the swagger.json specification. The default value is 'evesso' as currently defined in ESI)

The redirect URI, the client ID and the secret key are all get and set on [Eve Developer](https://developers.eveonline.com/applications).

```
>>> from esipy import EsiSecurity
>>> esi_security = EsiSecurity(
    app=esi_app,
    redirect_uri='https://example.com/oauth/callback',
    client_id='you client id',
    secret_key='the_secret_key',
)

## Authorization URI

To get the authorization URI to redirect the user :


Now to auth:
```python
# get the auth url
>>> security.get_auth_uri(scopes=['List', 'of', 'scopes'])  # return auth uri to redirect the user

# once you get the code from the auth, just set the oauth
>>> security.auth('code')  # this will set access_token, auth headers etc. 
```
