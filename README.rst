EsiPy |PyPI Version| |PyPI Python Version|
==========================================

|Build Status| |Coverage Status| |Code Health|

Documentation: |Documentation Status|

What is EsiPy
-------------

EsiPy is a python swagger client, taking advantages of `pyswagger`_
while rewriting some parts of it to be better used with EVE Online ESI
API.

Installation & Usage
--------------------

| Download it using pip
| ``pip install esipy``

Then to use it, you’ll have to define a client, an app and if you need
it, a security object.

Here are some quick example, for more informations, see the docs.

.. code:: python

    >>> from esipy import App
    >>> from esipy import EsiSecurity
    >>> from esipy import EsiClient

    # esi endpoint is used
    >>> app = App.create('https://esi.tech.ccp.is/latest/swagger.json')

    # security object, takes an app, redirect_uri, client_id, secret_key as argument
    >>> security = EsiSecurity(
        app,
        'http://exemple.com/oauth/callback',
        'client_id',
        'secret_key'
    )

    # client object have no mandatory parameters to be created, but you can presets
    # http headers, http_adapter, cache, security object...)
    >>> client = EsiClient(security)

Now to auth:

.. code:: python

    # get the auth url
    >>> security.get_auth_uri(scopes=['List', 'of', 'scopes'])  # return auth uri to redirect the user

    # once you get the code from the auth, just set the oauth
    >>> security.auth('code')  # this will set access_token, auth headers etc.

| Once this is done, you can query any endpoint (if the endpoint don’t
  require auth, skip the auth part for example).
| Operations are the different endpoint exposed from the API and are
  defined by endpoints OperationID

.. code:: python

    # get the list of incursions
    >>> incursion_operation = app.op['get_incursion']()
    >>> incursions = client.request(incursion_operation)

    # then access to the data as objects with the .data attribute, .headers for headers
    # for more information of response, you'll need to check the pyswagger doc.
    >>> incursions.data[0].staging_solar_system_id
    30004556

    >>> incursions.header['expires']
    "Fri, 16 Dec 2016 14:45:12 GMT"


    # if your endpoint need some parameter, just give it to the operation
    >>> character_location_operation = app.op['get_characters_character_id_location'](character_id=123456789)
    >>> char_location = client.request(character_location_operation)
    >>> char_location.data.station_id
    60004756

Contacts
--------

-  Kyria

   -  Github: @Kyria
   -  `TweetFleet Slack <https://www.fuzzwork.co.uk/tweetfleet-slack-invites/>`_: @althalus

.. _pyswagger: https://github.com/mission-liao/pyswagger

.. |PyPI Version| image:: https://img.shields.io/pypi/v/EsiPy.svg
   :target: https://pypi.python.org/pypi/EsiPy
.. |PyPI Python Version| image:: https://img.shields.io/pypi/pyversions/EsiPy.svg
   :target: https://pypi.python.org/pypi/EsiPy
.. |Documentation Status| image:: https://readthedocs.org/projects/esipy/badge/?version=latest
   :target: http://esipy.readthedocs.io/en/latest/?badge=latest
.. |Build Status| image:: https://travis-ci.org/Kyria/EsiPy.svg?branch=master
   :target: https://travis-ci.org/Kyria/EsiPy
.. |Coverage Status| image:: https://coveralls.io/repos/github/Kyria/EsiPy/badge.svg
   :target: https://coveralls.io/github/Kyria/EsiPy
.. |Code Health| image:: https://landscape.io/github/Kyria/EsiPy/master/landscape.svg?style=flat
   :target: https://landscape.io/github/Kyria/EsiPy/master
