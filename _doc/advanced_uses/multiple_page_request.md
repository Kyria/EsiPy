---
layout: base
section: advanced_uses/multiple_page_request
title: Multiple requests
---
# Multiple requests with threads

In some cases, you may need to do multiple requests at the same time to save time. You can achieve this using the `EsiClient.multi_request()` method.

<div class="alert alert-dismissible alert-danger">
    <strong>Attention:</strong> Unlike the "standard" request method, mutli_request returns a list of tuple (&lt;original request&gt;, &lt;response&gt;) for each operation it calls !
</div>

&nbsp;

## Parameters

It takes the following parameters:

Parameter | Type | Description
--- | --- | ---
reqs_and_resps | List | The list of operations created with the `App.op` dict
raw_body_only | Boolean | `True` if the response should stay raw json, `False` (default) if the response should be parsed
thread | Int | The number of thread in the pool used to do all calls [default: 20, max: 100]
opt | Dict | Dict for options used by the pyswagger BaseClient [default: None]

&nbsp;

## Example

```python
from esipy import App
from esipy import EsiClient

# create the app
app = App.create(url="https://esi.tech.ccp.is/latest/swagger.json?datasource=tranquility")

# create the client
client = EsiClient(
    retry_requests=True, 
    header={'User-Agent': 'Something CCP can use to contact you and that define your app'},
    raw_body_only=False,
)

# we want to know how much pages there are for The Forge
# so we make a HEAD request first
op = app.op['get_markets_region_id_orders'](
    region_id=10000002,
    page=1,
    order_type='all',
)
res = client.head(op)

# if we have HTTP 200 OK, then we continue
if res.status == 200:
    number_of_page = res.header['X-Pages'][0]

    # now we know how many pages we want, let's prepare all the requests
    operations = []
    for page in range(1, number_of_page+1):
        operations.append(
            app.op['get_markets_region_id_orders'](
                region_id=10000002,
                page=page,
                order_type='all',
            )
        )

    results = client.multi_request(operations)
    # results now contain a list of tuple with all (request, response) it called
```
