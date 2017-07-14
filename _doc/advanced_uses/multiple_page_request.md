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

# create the operation objects
# we know there are around 26 pages for The Forge

operations = []
for page in range(1,27):
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
