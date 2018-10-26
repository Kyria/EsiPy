---
layout: base
section: examples/caching_sso_jwt
title: Example - Caching SSO JWT informations
---
# Caching SSO & JWT

The goal here is to prevent the EsiSecurity object to make a request to get the different information from the EVE SSO discovery URL and JWKS

&nbsp;

## Requirements
You will need:
* A **persistant** cache
* `requests` 
* SSO discovery URL

&nbsp;

## Get the JWT / SSO informations and cache them

```python
import requests
from your.persistent.cache import Cache

# this is you cache, replace this by whatever you use (redis, memcached...)
cache = Cache()

# discovery URL
DISCOVERY_URL = 'https://login.eveonline.com/.well-known/oauth-authorization-server'

# get the SSO endpoints data
res = requests.get(DISCOVERY_URL)
res.raise_for_status()
sso_endpoints = res.json()

# get the JWKS. JWKS url is in the SSO discovery response
JWKS_URL = sso_endpoints['jwks_uri']
res = requests.get(JWKS_URL)
res.raise_for_status()
jwks = res.json()

# cache the data 1day (you can cache them more time if you want/need)
cache.set('sso_endpoints', sso_endpoints, 86400)
cache.set('jwks', jwks, 86400)
```

&nbsp;

## Use the cached data in EsiSecurity
```python
from esipy import EsiSecurity
from your.persistent.cache import Cache

cache = Cache()

# define some variables for the security object
SECRET_KEY = 'blablabla'
CLIENT_ID = 12345
CALLBACK_URI = 'localhost/callback'

# instanciate
security = EsiSecurity(
    client_id=CLIENT_ID,
    secret_key=SECRET_KEY,
    redirect_uri=CALLBACK_URI,
    sso_endpoints=cache.get('sso_endpoint', None),
    jwks_key=cache.get('jwks', None)
)
```

And there you go, now your security object will not request these informations but will use the data you provided from cache. 
