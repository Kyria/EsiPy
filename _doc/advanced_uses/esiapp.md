---
layout: base
section: advanced_uses/esiapp
title: EsiApp - Esi Meta Spec App 
---
# EsiApp

The EsiApp object provides an easy way to play with the [ESI Meta Swagger Spec](https://esi.tech.ccp.is/ui/?version=meta).<br>
It behave almost like the pyswagger app object, but can also return versionned swagger spec as app objects, while caching them.

&nbsp;

## How to use it

If you want to use it, you just need to import it and instanciate it. `EsiApp.__init__()` takes the following parameters:

Parameter | Type | Description
--- | --- | ---
cache | BaseCache | [Default: DictCache instance] The cache instance you want to use, just like EsiClient
cache_time | int | [Default: 86400] The number of seconds you want to keep versionned endpoint cached. `0` or `None` mean never expire.
cache_prefix | String | [Default: esipy] the cache key prefix used within EsiApp. 

```python
from esipy import EsiApp

app_without_cache = EsiApp(cache=None)
app_with_5min_cache = EsiApp(cache_time=300)
```

&nbsp;

Now you created your `EsiApp` instance, you can now either use endpoints like the pyswagger App, using `.op` attribute then calling that endpoints with an `EsiClient`.

You can also get ESI versionned endpoints using the related `operationId` as an attribute. For example `get_v2_swagger` ([Link](https://esi.tech.ccp.is/ui/?version=meta#/Swagger/get_v2_swagger)).

```python
# we use a client created in previous documentation page.

# get all ESI versions available
op = app.op['get_versions']()
res = client.request(op)

res.data
# returns :
# [u'dev', u'latest', u'legacy', u'v1', u'v2', u'v3', u'v4']

# now we'll get the "ESI V2" swagger spec
app_v2 = app.get_v2_swagger

print app_v2
# will display something like:
# <pyswagger.core.App object at 0x0649CA10>

# as the returned object if a fully working pyswagger.App object, we can use it normally
v2_op = app_v2.op['get_universe_system_kills']()
res = client.request(v2_op)

res.data[0]
# returns :
# {u'npc_kills': 94, u'system_id': 30035042, u'ship_kills': 2, u'pod_kills': 2}

# you can also verify that the URL is really /v2/ :
print v2_op[0].url
# returns:
# https://esi.tech.ccp.is/v2/universe/system_kills/
```

&nbsp;

## Clear cache for EsiApp
In case you set versionned app to never expire, you can invalidate so they will update on next call. 

To do this, you just need to call `EsiApp.clear_cached_endpoints()`. 

This will invalidate all cached data using the prefix `cache_prefix` defined when you initialized `EsiApp`. In case you want to invalidate older cached data, or specific data with another prefix, `EsiApp.clear_cached_endpoints()` also accept an argument `prefix` that will enforce the use of a specific cache_prefix instead of using the normal.

```python
app = EsiApp(cache_prefix="foo_v2")
# all cache key will be prefixed with foo_v2.

app.clear_cached_endpoints()
# this will clear all cached data using "foo_v2" as prefix.

# now let's say in another version of your app you had a "foo_v1", you can invalidate them (to free space)
# by using the following code (instead of manually looking for them within your cache or something): 

app.clear_cached_endpoints(prefix='foo_v1')
# this will clear all cached data using "foo_v1" as prefix, no matter what you defined in "cache_prefix".
```
