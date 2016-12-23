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

# To use it within a client, you have to give it to the client when you create it :
>>> esi_client = EsiClient(esi_security)
```

## Authorization URI

### Normal flow

To get the authorization URI to redirect the user :
```
>>> esi_security.get_auth_uri()
u'https://login.eveonline.com/oauth/authorize?response_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A65430%2Fcallback&client_id=foobarbazclient_id'

# if you need specific scopes, or state value
>>> esi_security.get_auth_uri(scopes=['your','scopes'], state='thestate')
u'https://login.eveonline.com/oauth/authorize?response_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A65430%2Fcallback&client_id=foobarbazclient_id&scope=your+scopes&state=thestate'
```

### Implicit flow

If you don't want to ship your secret_key in your app, you can use the implicit flow authentication process. To do this, add the `implicit=True` parameter
```
>>> esi_security.get_auth_uri(implicit=True)
u'https://login.eveonline.com/oauth/authorize?response_type=token&redirect_uri=http%3A%2F%2F91.121.112.50%3A65430%2Fcallback&client_id=a5b6c74daf704408bfa84f46975ed73a'
```
The main difference is the `response_type=token` value.


## Authentication

### Normal flow 
Now that you have the code from the previous user auth, you'll have to tell the security object to get the tokens.
```
>>> esi_security.auth('code')
```
And you are done. You can now do you requests and the security object (you gave to the client) will be automatically called. If the endpoint requires auth header, they will be automatically set.

### Implicit flow
With implicit flow, you get the `access_token` and `expires_in` values in the URL hash parameter.
Once you get them, you'll have to manually update the security object:
```
>>> esi_security.update_token({'access_token': 'the token', 'expires_in': 123456})
```


## Refresh
Each time you do a request, the security will check if it needs to refresh the access_token. If there are no refresh_token set, it will throw an AttributeError.

If you want to manually refresh it, you just have to call the refresh method:
```
>>> esi_security.refresh()
```

When a refresh is done while doing a request, a notification is send to the `after_token_refresh` [signal](advance/signal.md)


## Get the character informations
When you are logged in, you can get the character data with the verify method.
```
>>> esi_security.verify()
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