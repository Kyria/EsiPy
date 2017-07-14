---
layout: base
section: examples/using_refresh_token
title: 
---

# Using the refresh token

Here we'll see, step by step, how to use saved tokens from a previous login.

In the following steps, I will admit you saved somewhere your tokens, closed the previous python interpreter and opened a new one. 

<div class="alert alert-dismissible alert-info">
    Before starting this example, be sure you saved the tokens from the <a href="EsiPy/examples/sso_login_esipy/#step-4---use-the-code-and-get-the-tokens">SSO Login Example - Step 4</a> as we will use them here.
</div>

&nbsp;

## Step 1 - Creating EsiPy objects

Like in the login example, we'll need to create the esipy objects before beeing able to do anything.

```python
from esipy import App
from esipy import EsiClient
from esipy import EsiSecurity

app = App.create(url="https://esi.tech.ccp.is/latest/swagger.json?datasource=tranquility")

# replace the redirect_uri, client_id and secret_key values
# with the values you get from the STEP 1 !
security = EsiSecurity(
    app=app,
    redirect_uri='callback URL',
    client_id='you client id',
    secret_key='the_secret_key',
)

# and the client object, replace the header user agent value with something reliable !
client = EsiClient(
    retry_requests=True,
    header={'User-Agent': 'Something CCP can use to contact you and that define your app'},
    security=security
)
```

<div class="alert alert-dismissible alert-warning">
    If you don't know where to get the <strong>CALLBACK URL, CLIENT ID and SECRET KEY</strong>, please take a look at the <a href="EsiPy/examples/sso_login_esipy/#step-2---esipy-initialization">SSO Login Example - Step 2</a>.
</div>

&nbsp;

## Step 2 - Updating the security object

Now everything is ready, it's time to update the security object.

__As it probably pasts more than 20minute, we'll assume the access_token is expired so we will only care about the refresh_token__

```python
# to update the security object, 
security.update_token({
    'access_token': '',  # leave this empty
    'expires_in': -1,  # seconds until expiry, so we force refresh anyway
    'refresh_token ': 'YOUR_SAVED_REFRESH_TOKEN'
})
```

Now that we updated the security object, we have 2 choices:

* Either refresh the access token manually, so we can store the new token (better)
* Leave it like that and it will update itself with the first `EsiClient.request()` 

&nbsp;

## Step 3 - Updating the tokens

So we want to manually refresh the tokens, we just have to call one method to do this:

```python
tokens = security.refresh()
```

The `tokens` variable now contains your access token, refresh token, and the seconds left until expiry.<br>
__By doing this, your security object also knows these tokens and will use them automatically when doing requests__

```python
print tokens

{
  "access_token": "frenafeifafrbaefluerbfeainb",
  "token_type": "Bearer",
  "expires_in": 1200,
  "refresh_token": "fera48ftea4at64fr684fae"
}
```

<div class="alert alert-dismissible alert-success">
    Now you can make a query like in the <a href="EsiPy/examples/sso_login_esipy/#step-5---using-the-auth">SSO Login Example - Step 5</a>.

    <br> You can now see another example using <a href="https://github.com/Kyria/flask-esipy-example">Flask + Flask Login and sqlite as a database</a>.
</div>
