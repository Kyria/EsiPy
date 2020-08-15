---
layout: base
section: api/esiclient
title: API - EsiApp
---
# EsiClient

### `EsiClient(security=None, retry_requests=False, **kwargs)`
The EsiClient that will make the requests and do all the caching.

**Parameters:**
* **security** - the security object used for security checks and headers. Default is `None`
* **retry_requests** - flag to set auto retry on 5XX errors. Default False
* **headers** - A dict containing any header you want to add. Not adding `User-Agent` header will trigger a warn.
* **transport_adapter** - A HTTPAdapter implementation. Default is `requests.HTTPAdapter`
* **cache** - Any cache that implement `esipy.cache.BaseCache`
* **raw_body_only** - Disable the auto parsing of response if `True`. Default `False`
* **timeout** - Set a timeout for request. Default is `None` for no timeout.
* **signal_api_call_stats** - Allow to define a custom Signal to replace `API_CALL_STATS` using `signal_api_call_stats` when initializing the client
* **no_etag_body** - Disable the body from the result of the request if the response from ESI is a 304 (normal HTTP 304 behavior). Default is `False`

### `EsiClient.request(req_and_resp, **kwargs)`
Make a GET/POST/PUT/DELETE request, depending on the operation and return the response.

**Parameters:**
* **req_and_resp** - the operation object from pyswagger.App
* **raw_body_only** - define if we want the body to be parsed as object instead of staying a raw dict. Override value from `__init__`. Default `False`
* **raise_on_error** - raise an exception if a HTTP error happen. Default is `False`
* **opt** - Options for pyswagger.

### `EsiClient.head(req_and_resp, **kwargs)`
Make a HEAD request and return the response.

**Parameters:**
* **req_and_resp** - the operation object from pyswagger.App
* **raise_on_error** - raise an exception if a HTTP error happen. Default is `False`
* **opt** - Options for pyswagger.

### `EsiClient.multi_request(req_and_resp, threads=20, **kwargs)`
Make multiple request in parallel on the given operation (`req_and_resp`). Return a list of tuple containing the initial request object and the response.

**Parameters:**
* **req_and_respq** - A list of operation object from pyswagger.App
* **raw_body_only** - define if we want the body to be parsed as object instead of staying a raw dict. Override value from `__init__`. Default `False`
* **raise_on_error** - raise an exception if a HTTP error happen. Default is `False`
* **opt** - Options for pyswagger.
* **threads** - Number of concurrent workers to use. Default 20.
