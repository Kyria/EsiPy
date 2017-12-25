---
layout: base
section: advanced_uses/using_own_cache
title: Caching data
---
# Caching

EsiPy is packaged with some default caching mechanism you may use.

&nbsp;

## DummyCache
This is a fake cache, only used to disable caching. This is used by default when `cache` is set to `None` in the `EsiClient`.

&nbsp;

## DictCache
This is the default EsiPy cache. It stores everything in memory dictionary and may then use many memory on your system.

&nbsp;

## FileCache
This cache use `DiskCache` to work, thus requires you to install `diskcache` using `pip instal diskcache`. <br>
This cache will save data in files in a given directory, useful if you have many disc space but not much RAM.

When you instanciate the FileCache object, you'll have to give the following parameters:

Parameter | Type | Description
--- | --- | ---
path | String | The path where you want the files to be saved (diskCache will automatically create the directories if required)
settings | kwargs | The DiskCache parameters you may need. [See `Cache.__init__()` parameters](http://www.grantjenks.com/docs/diskcache/api.html#cache)

__Example__:
```python
# create the cache
from esipy.cache import FileCache
cache = FileCache(path="/tmp")

# and feed the client you create
client = EsiClient(cache=cache)
```

&nbsp;

## MemcachedCache
This cache use a `memcache.Client` object you give it as parameter to cache everything. <br>
__It requires you to have `python-memcached` installed.__

```python
# create the cache
import memcache
from esipy.cache import MemcachedCache
mc = memcache.Client(['127.0.0.1:11211'], debug=0)
cache = MemcachedCache(memcache_client=mc)

# and feed the client you create
client = EsiClient(cache=cache)
``` 

&nbsp;

## RedisCache
This cache use a `redis.Redis` object you give it as parameter to cache everything. <br>
__It requires you to have python [`redis` package](https://pypi.python.org/pypi/redis) installed.__

```python
# create the cache
import redis
from esipy.cache import RedisCache
redis_client = redis.Redis(host='localhost', port=6379, db=0)
cache = RedisCache(redis_client)

# and feed the client you create
client = EsiClient(cache=cache)
``` 

&nbsp;

## Your own custom cache for your custom needs
If you need a specific cache, because you already use your own, there's a way to define a valid cache for EsiPy.

1. First you need to inherit from `esipy.cache.BaseCache` and override the `get`, `set` and `invalidate` methods
2. You need to handle outdated data within the cache, as it's not done in EsiPy.

&nbsp;

__IMPORTANT:__ the caches keys used by EsiPy are tuples of frozendicts, which cannot be used everywhere. An existing `_hash` method allows you to get a md5 hash of the tuple, but you can define you own.

```python
from esipy.cache import BaseCache

# this is the minimum required
class YourCache(BaseCache):

    def set(self, key, value, timeout=300):
        # do something and store the value
        # timeout = 0 or None make the data never expire

    def get(self, key, default=None):
        # return the value or invalidate and return default

    def invalidate(self, key):
        # invalidate the cache key
```
