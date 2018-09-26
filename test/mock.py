# -*- encoding: utf-8 -*-
# pylint: skip-file
from __future__ import absolute_import

import datetime
import httmock


def make_expire_time_str(seconds=86400):
    """ Generate a date string for the Expires header
    RFC 7231 format (always GMT datetime)
    """
    date = datetime.datetime.utcnow()
    date += datetime.timedelta(seconds=seconds)
    return date.strftime('%a, %d %b %Y %H:%M:%S GMT')


def make_expired_time_str(seconds=86400):
    """ Generate an expired date string for the Expires header
    RFC 7231 format (always GMT datetime).
    """
    date = datetime.datetime.utcnow()
    date -= datetime.timedelta(seconds=seconds)
    return date.strftime('%a, %d %b %Y %H:%M:%S GMT')


@httmock.urlmatch(
    scheme="https",
    netloc=r"login\.eveonline\.com$",
    path=r"^/v2/oauth/token$"
)
def oauth_token(url, request):
    """ Mock endpoint to get token (auth / refresh) """
    if 'fail_test' in request.body:
        return httmock.response(
            status_code=400,
            content={'message': 'Failed successfuly'}
        )

    if 'no_refresh' in request.body:
        return httmock.response(
            status_code=200,
            content={
                'access_token': 'access_token',
                'expires_in': 1200,
            }
        )

    return httmock.response(
        status_code=200,
        content={
            'access_token': 'access_token',
            'expires_in': 1200,
            'refresh_token': 'refresh_token'
        }
    )


@httmock.urlmatch(
    scheme="https",
    netloc=r"login\.eveonline\.com$",
    path=r"^/v2/oauth/revoke$"
)
def oauth_revoke(url, request):
    if (('token_type_hint=refresh_token' in request.body
        and 'token=refresh_token' in request.body) or
       ('token_type_hint=access_token' in request.body and
       'token=access_token' in request.body)):
        return httmock.response(
            status_code=200,
            content=''
        )
    else:
        raise Exception('Revoke message not properly set: %s' % request.body)


@httmock.urlmatch(
    scheme="https",
    netloc=r"login\.eveonline\.com$",
    path=r"^/\.well-known/oauth-authorization-server$"
)
def oauth_authorization_server(url, request):
    """ return the content of the file of the same name """
    with open('test/resources/oauth-authorization-server.json', 'r') as fd:
        return httmock.response(
            status_code=200,
            content=fd.read()
        )


@httmock.urlmatch(
    scheme="https",
    netloc=r"login\.eveonline\.com$",
    path=r"^/oauth/jwks$"
)
def oauth_jwks(url, request):
    """ return the content of the file of the same name """
    with open('test/resources/jwks.json', 'r') as fd:
        return httmock.response(
            status_code=200,
            content=fd.read()
        )


@httmock.urlmatch(
    scheme="https",
    netloc=r"esi\.evetech\.net$",
    path=r"^/latest/incursions/$"
)
def public_incursion(url, request):
    """ Mock endpoint for incursion.
    Public endpoint
    """
    return httmock.response(
        headers={'Expires': make_expire_time_str()},
        status_code=200,
        content=[
            {
                "type": "Incursion",
                "state": "mobilizing",
                "staging_solar_system_id": 30003893,
                "constellation_id": 20000568,
                "infested_solar_systems": [
                    30003888,
                ],
                "has_boss": True,
                "faction_id": 500019,
                "influence": 1
            }
        ]
    )


@httmock.urlmatch(
    scheme="https",
    netloc=r"esi\.evetech\.net$",
    path=r"^/latest/incursions/$"
)
def public_incursion_no_expires(url, request):
    """ Mock endpoint for incursion.
    Public endpoint without cache
    """
    return httmock.response(
        status_code=200,
        content=[
            {
                "type": "Incursion",
                "state": "mobilizing",
                "staging_solar_system_id": 30003893,
                "constellation_id": 20000568,
                "infested_solar_systems": [
                    30003888,
                ],
                "has_boss": True,
                "faction_id": 500019,
                "influence": 1
            }
        ]
    )


@httmock.urlmatch(
    scheme="https",
    netloc=r"esi\.evetech\.net$",
    path=r"^/latest/incursions/$"
)
def public_incursion_no_expires_second(url, request):
    """ Mock endpoint for incursion.
    Public endpoint without cache
    """
    return httmock.response(
        status_code=200,
        content=[
            {
                "type": "Incursion",
                "state": "established",
                "staging_solar_system_id": 30003893,
                "constellation_id": 20000568,
                "infested_solar_systems": [
                    30003888,
                ],
                "has_boss": True,
                "faction_id": 500019,
                "influence": 1
            }
        ]
    )


@httmock.urlmatch(
    scheme="https",
    netloc=r"esi\.evetech\.net$",
    path=r"^/latest/characters/(\d+)/location/$"
)
def auth_character_location(url, request):
    """ Mock endpoint for character location.
    Authed endpoint that check for auth
    """
    return httmock.response(
        headers={'Expires': make_expire_time_str()},
        status_code=200,
        content={
            "station_id": 60004756,
            "solar_system_id": 30002543
        }
    )


@httmock.urlmatch(
    scheme="https",
    netloc=r"esi\.evetech\.net$",
    path=r"^/latest/status/$"
)
def eve_status(url, request):
    """ Mock endpoint for character location.
    Authed endpoint that check for auth
    """
    return httmock.response(
        headers={
            'Expires': make_expire_time_str(1),
            'Etag': '"esipy_test_etag_status"'
        },
        status_code=200,
        content={
            "players": 29597,
            "server_version": "1313143",
            "start_time": "2018-05-20T11:04:30Z"
        }
    )


@httmock.urlmatch(
    scheme="https",
    netloc=r"esi\.evetech\.net$",
    path=r"^/latest/status/$"
)
def eve_status_noetag(url, request):
    """ Mock endpoint for character location.
    Authed endpoint that check for auth
    """
    return httmock.response(
        headers={
            'Expires': make_expire_time_str(1),
        },
        status_code=200,
        content={
            "players": 29597,
            "server_version": "1313143",
            "start_time": "2018-05-20T11:04:30Z"
        }
    )


@httmock.urlmatch(
    scheme="https",
    netloc=r"esi\.evetech\.net$",
    path=r"^/latest/universe/ids/$"
)
def post_universe_id(url, request):
    """ Mock endpoint for character location.
    Authed endpoint that check for auth
    """
    return httmock.response(
        headers={'Expires': make_expire_time_str()},
        status_code=200,
        content={
            "characters": [
                {
                    "id": 123456789,
                    "name": "Foo"
                }
            ]
        }
    )


@httmock.urlmatch(
    scheme="https",
    netloc=r"esi\.evetech\.net$",
    path=r"^/latest/incursions/$"
)
def public_incursion_warning(url, request):
    """ Mock endpoint for incursion.
    Public endpoint without cache
    """
    return httmock.response(
        status_code=200,
        headers={"Warning": "199 - This endpoint has been updated."},
        content=[
            {
                "type": "Incursion",
                "state": "established",
                "staging_solar_system_id": 30003893,
                "constellation_id": 20000568,
                "infested_solar_systems": [
                    30003888,
                ],
                "has_boss": True,
                "faction_id": 500019,
                "influence": 1
            }
        ]
    )


@httmock.urlmatch(
    scheme="https",
    netloc=r"esi\.evetech\.net$",
    path=r"^/latest/incursions/$"
)
def public_incursion_server_error(url, request):
    """ Mock endpoint for incursion.
    Public endpoint without cache
    """
    public_incursion_server_error.count += 1
    return httmock.response(
        status_code=500,
        content={
            "error": "broke",
            "count": public_incursion_server_error.count
        }
    )


public_incursion_server_error.count = 0


@httmock.urlmatch(
    scheme="https",
    netloc=r"esi\.evetech\.net$",
    path=r"^/latest/incursions/$"
)
def public_incursion_expired(url, request):
    """ Mock endpoint for incursion.
    Public endpoint returning Expires value in the past
    """
    return httmock.response(
        headers={'Expires': make_expired_time_str()},
        status_code=200,
        content=[
            {
                "type": "Incursion",
                "state": "mobilizing",
                "staging_solar_system_id": 30003893,
                "constellation_id": 20000568,
                "infested_solar_systems": [
                    30003888,
                ],
                "has_boss": True,
                "faction_id": 500019,
                "influence": 1
            }
        ]
    )


@httmock.urlmatch(
    scheme="https",
    netloc=r"esi\.evetech\.net$",
    path=r"^/swagger.json$"
)
def meta_swagger(url, request):
    """ Mock endpoint for incursion.
    Public endpoint returning Expires value in the past
    """
    if request.headers.get('etag') == '"esipyetag"':
        return httmock.response(
            headers={
                'Expires': make_expire_time_str(),
                'Etag': '"esipyetag"'
            },
            status_code=304,
            content={}
        )

    swagger_json = open('test/resources/meta_swagger.json')
    resp = httmock.response(
        headers={
            'Expires': make_expire_time_str(),
            'Etag': '"esipyetag"'
        },
        status_code=200,
        content=swagger_json.read()
    )
    swagger_json.close()
    return resp


@httmock.urlmatch(
    scheme="https",
    netloc=r"esi\.evetech\.net$",
    path=r"^/v1/swagger.json$"
)
def v1_swagger(url, request):
    """ Mock endpoint for incursion.
    Public endpoint returning Expires value in the past
    """
    swagger_json = open('test/resources/swagger.json')

    resp = httmock.response(
        headers={'Expires': make_expire_time_str()},
        status_code=200,
        content=swagger_json.read()
    )
    swagger_json.close()
    return resp


@httmock.all_requests
def non_json_error(url, request):
    """ Mock endpoint for non json returns (usually errors).
    """
    return httmock.response(
        headers={},
        status_code=502,
        content='<html><body>Some HTML Errors</body></html>'
    )


_all_auth_mock_ = [
    oauth_token,
    oauth_authorization_server,
    oauth_jwks,
    auth_character_location,
]

_swagger_spec_mock_ = [
    meta_swagger,
    v1_swagger
]
