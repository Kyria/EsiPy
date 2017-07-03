---
layout: base
---
# EsiPy

## What is EsiPy
EsiPy is a python swagger client that will parse the `swagger.json` to know the structure of the API.

It takes advantages of [pyswagger](https://github.com/mission-liao/pyswagger), while rewriting some parts of it: <br>
- Client <br>
- Security

It also add more features to the client:  <br>
- Caching <br>
- Auth processes / headers <br>
- Signals

EsiPy support multiple version of CPython (`2.7`, `3.3`, `3.4`, `3.5`), `PyPy2` and `PyPy3`.
