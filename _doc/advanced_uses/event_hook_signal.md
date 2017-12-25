---
layout: base
section: advanced_uses/event_hook_signal
title: Signals subscriptions 
---
# Signals

## What are signals

Signals are "events" that will be triggered in some circumstances. When triggered, they will call all "callable" objects (functions, object methods, ...) that are hooked on the signal.

To hook to any signal, just call the `add_receiver` method from the signal you want to subscribe.<br>
To remove your subscription to a signal, call the `remove_receiver` method from the signal.

&nbsp;

## Example

To have a little more details on how it work, let's take the `after_token_refresh` signal, which is triggered when the token is refreshed while the app is doing a `EsiClient.request()` call.<br>
Description of this signal is in the [next section of this page](#after_token_refresh).

```python
# first we reate a function that'll wait for the signal parameters
# kwargs is used to prevent error if CCP adds more thing in the /oauth/token response
def after_token_refresh_hook(access_token, refresh_token, expires_in, **kwargs):
	print "We got new token: %s" % access_token
	print "refresh token used: %s" % refresh_token
	print "Expires in %d" % expires_in

# now we hook to the signal
from esipy.event import after_token_refresh
after_token_refresh.add_receiver(after_token_refresh_hook)

# let's say you have a security object initialized and a client (see [SSO Authentification])
# you wait for 20minutes, the token to expires then you do a request (any with authentification required)
op = app.op['get_characters_character_id_wallet'](
    character_id=123456789
)
wallet = esiclient.request(op)

# This will also print the following
We got new token: AZERDFGJGUTR35GI7YAHGG318734G9
refresh token used: J31498HDF83G0187GD40318G
Expires in 1200
```

&nbsp;

## List of signals

### __AFTER_TOKEN_REFRESH__

This triggered with a token update while a `EsiClient.request()` is done. This is *not* triggered if the user manually call `EsiSecurity.update()`.

Arguments | Type | Description
--- | --- | ---
access_token | String | The new access token used to log in
refresh_token | String | The refresh token used to refresh
expires_in | int | The token validity time in seconds
token_type | String | The token type returned
**kwargs | Dict | Any other values CCP may add in the future and not yet in this doc

### __API_CALL_STATS__

This signal is triggered after each requests done. <br>
The only purpose of this request is to monitor api calls.

__IMPORTANT:__ Please keep in mind that, if you do time consuming tasks using this event, your calls will be slowed ! Consider using async / parallel tasks here.

Arguments | Type | Description
--- | --- | ---
url | String | The url called
status_code | int | The status code of the request
elapsed_time | int | The elapsed time to get the response in seconds
message | String | JSON response string only if status_code is not 200, else None.

&nbsp;