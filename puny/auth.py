from pecan import request, conf

import requests


def check_permissions():
    '''
    Ping the IndieAuth token endpoint to validate the request.
    '''

    # first, check and see if an authorization header is provided
    auth_header = request.headers.get('Authorization')
    if auth_header is None:
        # if not, check to see if an `access_token` parameter
        # has been passed in, and synthesize the header.
        if request.params.get('access_token'):
            auth_header = 'Bearer ' + request.params['access_token']

    # if we don't have an auth header, deny
    if not auth_header:
        return False

    # ping the token endpoint
    result = requests.get(
        conf.indieauth.token,
        headers={'Authorization': auth_header, 'Accept': 'application/json'},
    )

    # ensure that the token is valid and is valid for us with the
    # correct scopes
    if result.status_code in (200, 201):
        request.auth = result.json()
        if (
            (request.auth['me'] == conf.indieauth.me)
            or (request.auth['me'][:-1] == conf.indieauth.me)
        ):

            # TODO: check scopes
            if 'create' in request.auth['scope']:
                return True

    return False
