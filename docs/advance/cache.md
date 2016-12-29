# Caching

EsiPy is packaged with some default caching mechanism you may use.

Each cache provides the following methods: `get(key, default=None)`, `set(key, value, timeout=300)`, `invalidate(key)`.



## DummyCache
This is a fake cache, only used to disable caching. This is used by default when `cache` is set to `None` in the `EsiClient`.



## DictCache
This is the default EsiPy cache. It stores everything in memory dictionary and may then use many memory on your system.



## FileCache
This cache use `DiskCache` to work, thus requires you to install `diskcache` using `pip instal diskcache`. This cache will save data in files in a given directory, useful if you have many disc space but not much RAM.

When you instanciate the FileCache object, you'll have to give the following parameters:

Parameter | Type | Description
--- | --- | ---
path | String | The path where you want the files to be saved (diskCache will automatically create the directories if required)
settings | kwargs | The DiskCache parameters you may need. [See `Cache.__init__()` parameters](http://www.grantjenks.com/docs/diskcache/api.html#cache)



## MemcachedCache
This cache use a `memcache.Client` object you give it as parameter to cache everything. It requires you to have `python-memcached` installed.



## You own custom cache for your custom needs
In case you need a specific cache that's not already provided here, you can create your own. There are only two requirements: you have to inherit `BaseCache` and your cache must handle outdated data itself.

Also, as the cache keys are not simple string but tuples of frozendicts, the `BaseCache` provides a simple `_hash` function (using md5) that will return a string to be used as key for your cache (You can make your own if you want to).


