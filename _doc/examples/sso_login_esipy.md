---
layout: base
section: examples/sso_login_esipy
title: Example - SSO Login with Esipy
---
# SSO Login using EsiPy

Here we'll see, step by step, how to log in, using EVE Online SSO and EsiPy.

<div class="alert alert-dismissible alert-info">
    <strong>Reminder:</strong> This is only a basic example to go through the full login process. <br>
    It doesn't use any sort of webserver, database or anything but just manual actions to explain how it works!
</div>

## Step 1 - Creating an application CCP side.

Go to [EVE Online Developers](https://developers.eveonline.com/applications), log in and click on `Create new application`

Fill the fields like this:

* __Name:__ The name of your app (your choice)
* __Description:__ A description of your app
* __Connection Type:__ Choose "Authentication & API Access"
* __Permissions:__ Add the scope `esi-wallet.read_character_wallet.v1` in the right box (you can put everything if you want too)
* __Callback URL:__ Put `http://localhost:65432/callback/` (it doesn't matter actually, it's just to have something)

Then click on `Create Application`

On the next page, you'll see your application you just created. Click on the `View Application` button.

Here you can find the following information we'll need after: 

* Client ID
* Secret Key
* Callback URL

&nbsp;

## Step 2 - EsiPy initialization

If you didn't already create a virtualenv and install EsiPy, here are the steps to follow:

```bash
mkdir esipy_sso_example
cd esipy_sso_example
virtualenv venv
source venv/bin/activate
pip install esipy
```

Now, in the python console, we'll create the `App`, `EsiClient` and `EsiSecurity`:

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

Once this is done, we can try to log a user in !

&nbsp;

## Step 3 - Log a user in

To log a user, we will need to go to CCP SSO Login form, log in, then we will be redirected to our callback URL with a code we can use.

__Login and get the code__

```python
# this print a URL where we can log in
print security.get_auth_uri(scopes=['esi-wallet.read_character_wallet.v1'])
```

The URL will have the form of <br>
```https://login.eveonline.com/oauth/authorize?response_type=code&redirect_uri=[CALLBACK URL]&client_id=[CLIENT ID]&scope=esi-wallet.read_character_wallet.v1```

Copy the URL and paste it in your browser. You will be prompted to log in, accept the scope then redirected to our callback.

__Of course, you will get a 404 error, BUT__ check the URL: you should notice a `?=code=xxxxxxxx` within. <br>
__Get this code, all of it, we'll use it very soon.__

&nbsp;

## Step 4 - Use the code and get the tokens

Now with the code, we can get our tokens:

```python
# YOUR_CODE is the code you got from Step 3. (do not forget quotes around it)
tokens = security.auth('YOUR_CODE')
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

You can save these values somewhere if you want (and then they can be used in [the refresh token example](/EsiPy/examples/using_refresh_token/)).

&nbsp;

## Step 5 - Using the auth

Now that you are authed, we can do a real request on the ESI API: 

```python
# use the verify endpoint to know who we are
api_info = security.verify()

# api_info contains data like this
# {
#   "Scopes": "esi-wallet.read_character_wallet.v1",
#   "ExpiresOn": "2017-07-14T21:09:20",
#   "TokenType": "Character",
#   "CharacterName": "SOME Char",
#   "IntellectualProperty": "EVE",
#   "CharacterOwnerHash": "4raef4rea8aferfa+E=",
#   "CharacterID": 123456789
# }

# now get the wallet data
op = app.op['get_characters_character_id_wallet'](
    character_id=api_info['CharacterID']
)
wallet = client.request(op)

# and to see the data behind, let's print it
print wallet.data
```

<div class="alert alert-dismissible alert-success">
    Now you are done, next step is either see how to <a href="/EsiPy/examples/using_refresh_token/">use refresh token</a> or see another example using <a href="https://github.com/Kyria/flask-esipy-example">Flask + Flask Login and sqlite as a database</a>.
</div>