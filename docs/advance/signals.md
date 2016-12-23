# Signals

Signals are "events" that will be triggered in some circumstances and they can have one or more functions attached as receivers of the event.
These functions will be called automatically when the signal is fired.

To subscribe to any of these signals, you just need to import it and add your receiver to it. In the same way, you also can remove an receiver from an signal whenever you want, in case you don't want the event to trigger your receiver again.


```python
>>> from esipy.event import after_token_refresh
>>> after_token_refresh.add_receiver(your_receiver_function)  # from now, your_receiver_function will be triggered with this signal

...

>>> after_token_refresh.remove_receiver(your_receiver_function)  # once you do this, your_receiver_function will never be triggered, unless you add it again
```



## List of signals
####__after_token_refresh__

This signal is triggered as soon as the refresh token is automatically updated by the ESI Client (not triggered if you manually call the EsiSecurity.update() method).

List of argument given to the receivers :

Arguments | Type | Description
--- | --- | ---
access_token | String | The new access token used to log in
refresh_token | String | The refresh token used to refresh
expires_in | int | The token validity time in seconds

