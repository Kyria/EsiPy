---
layout: base
section: getting_started/basic_usage
title: Basic Usage
---
# Using EsiPy

To use EsiPy, you will need to define at least two objects:
* an `App`
* an `EsiClient`

&nbsp;

## App

The `App` object will deal with everything that comes from swagger: 
* Parsing the swagger spec
* Generating operations
* Validate parameters

To use it, you can either instanciate it directly, or use the `EsiApp` object that also use cache. <br>
Exemple:
```python
# Using EsiApp [recommended]
from esipy import EsiApp
esi_app = EsiApp()
app = esi_app.get_latest_swagger

# Using App, both "app" are the same at the end
# DO NOT USE "App", since there's no cache etc. Unless you plan to do it yourself!
from esipy import App

# App.create(url, strict=True)
# with url = the swagger spec URL, leave strict to default
app = App.create(url="https://esi.evetech.net/latest/swagger.json?datasource=tranquility")
```

**This process can be slow (easily ~40sec per version you get). If you use `EsiApp` this will be only once per version / per process you start, or if you use a persistent cache, only once per version**

<div class="alert alert-dismissible alert-info">
    For more details about EsiApp, please see <a href="/EsiPy/getting_started/esiapp/">this page</a>.
</div>

&nbsp;

## EsiClient

The `EsiClient` is the client object that will be used to do the actual requests.<br>
It uses the pyswagger `BaseClient`. it also adds some useful features:
* Caching results (can be disabled / customized)
* Auto retry requests on 5XX HTTP Errors
* Threaded requests (multiple requests at the same time)

```python
from esipy import EsiClient

# basic client, for public endpoints only
client = EsiClient(
    retry_requests=True,  # set to retry on http 5xx error (default False)
    headers={'User-Agent': 'Something CCP can use to contact you and that define your app'},
    raw_body_only=False,  # default False, set to True to never parse response and only return raw JSON string content.
)
```

&nbsp;

## Requesting an endpoint

To request an endpoint, you first need its `operationId` (you can find this information while browsing the swagger specifications).<br>
For example, the `operationId` to get the market orders in a region is `get_markets_region_id_orders`.

Once you have the `operationId` you can generate the operation object (which is actually a (request, response) tuple you shouldn't manually edit), then use it to make the request.

```python
# generate the operation tuple
# the parameters given are the actual parameters the endpoint requires
market_order_operation = app.op['get_markets_region_id_orders'](
    region_id=10000002,
    type_id=34,
    order_type='all',
)

# do the request
response = client.request(market_order_operation)

# use it: response.data contains the parsed result of the request.
print response.data[0].price

# to get the headers objects, you can get the header attribute
print response.header
```

&nbsp;

## Requesting without parsing the response

In some cases, you may not want EsiPy to parse the response from your request because you need performances. Parsing the result may double, or even worse, the time required to make a request and get the results. 

To do this, you need to use the `raw_body_only`, either when creating your `EsiClient` (see above) or when doing the request:

```python
raw_response = client.request(market_order_operation, raw_body_only=True)

# this prints "None"
print raw_response.data

# this print the json string from the response
print raw_response.raw

# you may also convert it to an object
import json
json_response = json.loads(raw_response.raw)
``` 

&nbsp;

## Requesting endpoints using POST/DELETE/PUT instead of GET

If you are want to use an endpoint that is not "GET" (meaning, it's one of the others, PUT/POST/...) you will actually use it like if it is a GET.

What it means is that the method of the request (GET/PUT/...), how to provide arguments, parameters, message body, etc, is fully managed within pyswagger.

So all you need is an operation object, filled with the parameters you might want and do the request.

```python
# POST request on /universe/ids/
post_operation = app.op['post_universe_ids'](names=['Althalus Stenory'])

# do the request
response = client.request(post_operation)

print response.data
# displays: {u'characters': [{u'id': 961633431, u'name': u'Althalus Stenory'}]}
```
