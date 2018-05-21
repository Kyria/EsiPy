---
layout: base
section: api/esiapp
title: API - EsiApp
---
# EsiApp

### `EsiApp(**kwargs)`
The EsiPy App wrapper that will deal with `pyswagger.App` and caching.

**Parameters:**
* **cache** - the cache object to use that inherits from `esipy.cache.BaseCache`. Default is `DictCache`
* **cache_time** - the default timeout for any specifications initiated. Default is `86400` (1 day), `0` to never expire, and `None` to use endpoint expiration.
* **cache_prefix** - the prefix used in every cache key. Default is `esipy`.
* **meta_url** - the meta swagger specification to use. By default it will use [https://esi.evetech.net/swagger.json](https://esi.evetech.net/swagger.json)
* **datasource** - The EVE datasource to use for specifications. Default is `tranquility`. 

### `EsiApp.op`
The `op` attribute allows to use any operation defined in the meta specification.

Basic exemple:
```python
app = EsiApp()
verify_operation = app.op['get_verify'](token="sometoken")
```

### `EsiApp.<any_swagger_spec_operation>`
These operations allows to get the `pyswagger.App` object related to this operation.

Exemple:
* `EsiApp.get_v1_swagger` will return the App for V1 specification
* `EsiApp.get_v2_swagger` will return the App for V2 specification
* `EsiApp.get_v3_swagger` will return the App for V3 specification
* `EsiApp.get_v4_swagger` will return the App for V4 specification
* `EsiApp.get_latest_swagger` will return the App for latest specification
* `EsiApp.get_dev_swagger` will return the App for dev specification
* `EsiApp.get_legacy_swagger` will return the App for legacy specification
* `EsiApp.get__latest_swagger` will return the App for latest specification, with real version number instead of `/latest`
* `EsiApp.get__dev_swagger` will return the App for dev specification, with real version number instead of `/dev`
* `EsiApp.get__legacy_swagger` will return the App for legacy specification, with real version number instead of `/legacy`

```python
app = EsiApp()
app_v1 = app.get_v1_swagger
operation = app_v1.op['some_operation']()
```

### `EsiApp.clear_cached_endpoints(prefix=None)`
Invalidate all cached endpoints, meta included.

Loop over all meta endpoints to generate all cache key the invalidate each of them. 
Doing it this way will prevent the app not finding keys as the user may change its prefixes Meta endpoint will be updated upon next call.

**Parameters:**
* **prefix** - the cache key prefix you want to use to invalidate keys. If `None` use the current instance `self.cache_prefix`