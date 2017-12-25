---
layout: base
section: advanced_uses/esiapp
title: EsiApp - Esi Meta Spec App 
---
# EsiApp

The EsiApp object provides an easy way to play with the [ESI Meta Swagger Spec](https://esi.tech.ccp.is/ui/?version=meta).<br>
It behave almost like the pyswagger app object, but can also return versionned swagger spec as app objects, while caching them.

## How to use it

If you want to use it, you just need to import it and instanciate it. `EsiApp.__init__()` takes the following parameters:

Parameter | Type | Description
--- | --- | ---
cache | BaseCache | [Default: DictCache instance] The cache instance you want to use, just like EsiClient
cache_time | int | [Default: 86400] The number of seconds you want to keep versionned endpoint cached. `0` or `None` mean never expire.

```python
from esipy import EsiApp

app_without_cache = EsiApp(cache=None)
app_with_5min_cache = EsiApp(cache_time=300)
```

Now you created your `EsiApp` instance, you can now either se endpoints like the pyswagger App, using `.op` attribute then calling that endpoints with an `EsiClient`<br>
or you can get ESI versionned endpoints using the related `operationId` as an attribute. For example [`get_v2_swagger`](https://esi.tech.ccp.is/ui/?version=meta#/Swagger/get_v2_swagger).

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

## Force update endpoints
In case you set versionned app to never expire, you can force them to refresh on next call. 

To do this, you just need to call `EsiApp.force_update()`. This will update the Meta Spec within the `EsiApp` object, but also invalidate all cached data, to make sure they will update next time you use them.