# Usage

To use EsiPy, you'll have to define a client, an app, and if you need it, a security object (see the [SSO Authentication](auth.md) section)


## The App

The App is an object that will deal with the swagger endpoint: parsing, exposing endpoints (operations) and checking the request parameter and response to verify everything match the swagger.json specification for this endpoint.

The App object is actually a pyswagger object. You can import it from esipy as a shortcut is set there. Then just use the `App.create()' to get you configured app object.
```
>>> from esipy import App
>>> esi_app = App.create('https://esi.tech.ccp.is/latest/swagger.json?datasource=tranquility')
```
And you are done. 

For more detail about this object, please read the pyswagger documentation.


## The EsiClient

The client is only here to do some basic tasks : 
- [Caching](advance/cache.md)
- Doing the requests
- Asking the security object to do its job.

All EsiClient init parameters are optional and it will work with a simple: 
```
>>> from esipy import EsiClient
>>> esi_client = EsiClient()
```

Here are the parameters you can pass the `EsiClient()`:
Parameter | Type | Description
--------- | ---- | -----------
security  | EsiSecurity | The security object that will manage the security parts
headers   | Dict | A dict with all header keys/value you may want to overwrite
cache     | BaseCache | The caching mecanism to use. To disable it, set it to `None`
transport_adapter | HTTPAdapter | The HTTPAdapter object you want to use for your requests


## Operations

Once you have both Client and App set, you can make requests.

First you need to get the operation object of the endpoint you want to get. To do this, simply use the app object:
```
# generic example
>>> operation = esi_app.op['operationId']()

# incursions example
>>> incursion_operation = esi_app.op['get_incursions']()
```

If your endpoint is waiting for path parameters or query parameters, this is also the place where you set them.
```
# market order endpoints (jita, all order type, tritanium)
>>> market_order_operation = esi_app.op['get_markets_region_id_orders'](
    region_id=10000002,
    type_id=34,
    order_type='all',
)


## Make the request and get the response.

Now you have your operations set, let's make the actual query using EsiClient.request()
```
>>> incursions = esi_client.request(incursion_operation)

# then access to the data as objects with the .data attribute, .header for headers
# for more information of response, you'll need to check the pyswagger doc.
>>> incursions.data[0].staging_solar_system_id
30004556

>>> incursions.header['Expires'][0]
"Fri, 16 Dec 2016 14:45:12 GMT"

# if you want the raw content (string), use the .raw attribute:
>>> incursions.raw
'[{"type": "Incursion", "state": "mobilizing", "influence": 1.0, "has_boss": true, "faction_id": 500019, "constellation_id": 20000510, "staging_solar_system_id": 30003497, "infested_solar_systems": [30003493, 30003494, 30003495, 30003496, 30003497, 30003498]}, {"type": "Incursion", "state": "mobilizing", "influence": 0.0, "has_boss": false, "faction_id": 500019, "constellation_id": 20000182, "staging_solar_system_id" ... ]'
```

As the response content is parsed and put into a structure according to the swagger specifications, for some endpoint this process can be really slow (market orders, we are looking at you).

In this case, if you don't want it to be parse, you'll have to add the `raw_body_only=True` parameter to the request() call (it may save up to 50-70% of time depending on the endpoint). You'll  then only have access to the raw content you can parse using `json.loads()`:
```
>>> incursions = esi_client.request(incursion_operation, raw_body_only=True)
>>> incursions.data[0].staging_solar_system_id
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: 'NoneType' object has no attribute '__getitem__'

>>> incursions.header['Expires'][0]
'Fri, 23 Dec 2016 14:05:05 GMT'

>>> incursions.raw
'[{"type": "Incursion", "state": "mobilizing", "influence": 1.0, "has_boss": true, "faction_id": 500019, "constellation_id": 20000510, "staging_solar_system_id": 30003497, "infested_solar_systems": [30003493, 30003494, 30003495, 30003496, 30003497, 30003498]}, {"type": "Incursion", "state": "mobilizing", "influence": 0.0, "has_boss": false, "faction_id": 500019, "constellation_id": .... ]'

>>> json.loads(incursions.raw)
[{u'staging_solar_system_id': 30003497, u'has_boss': True, u'infested_solar_systems': [30003493, 30003494, 30003495, 30003496, 30003497, 30003498], u'influence': 1.0, u'faction_id': 500019, u'state': u'mobilizing', u'constellation_id': 20000510, u'type': u'Incursion'}, {u'staging_solar_system_id': 30001253, u'has_boss': False, u'infested_solar_systems': [30001248, 30001249, 30001250, 30001251, 30001252, 30001253, 30001246, 30001247], u'influence': 0.0, u'faction_id': 500019, u'state': u'mobilizing', u'constellation_id': 20000182, u'type': u'Incursion'}, ... ]
```