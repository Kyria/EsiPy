---
layout: base
section: advanced_uses/http_2
title: EsiPy and HTTP/2 
---
# EsiPy and HTTP/2

Currently, requests, and thus EsiPy, only supports HTTP/1.

## Using `hyper`

One solution, and probably the easiest, is to use the `hyper` library.<br>
You can find all `hyper` documentation [here](https://hyper.readthedocs.io/en/latest/).

To install it, simply do `pip install hyper`

<div class="alert alert-dismissible alert-danger">
    <strong>Attention:</strong> it looks like hyper have some (strong) installation requirements. Don't forget to <a href="https://hyper.readthedocs.io/en/latest/quickstart.html#installation-requirements">take a look at them</a>
</div>

&nbsp;

## `hyper` and `EsiPy`

Once you installed `hyper`, you need to tell `EsiPy` to use it.<br>
For this, you need to create a `HTTP20Adapter` from `hyper` and provide it to `EsiPy` (`EsiClient` and `EsiSecurity` may use it)

```python
# import the hyper HTTPAdapter
from hyper.contrib import HTTP20Adapter

# create the EsiSecurity, adding transport_adapter adapter parameter
security = EsiSecurity(
    app=app,
    redirect_uri='https://callback.com/you/set/on/developers/eveonline',
    client_id='you client id',
    secret_key='the_secret_key',
    transport_adapter=HTTP20Adapter(), 
)

# create the EsiClient, adding transport_adapter adapter parameter
client = EsiClient(
    retry_requests=True,  
    headers={'User-Agent': 'Something CCP can use to contact you and that define your app'},
    raw_body_only=False,
    transport_adapter=HTTP20Adapter(), 
)
```

And now, EsiPy will use HTTP/2
