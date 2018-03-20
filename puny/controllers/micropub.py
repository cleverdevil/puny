from pecan import expose, request, response, abort, conf
from pecan.hooks import PecanHook
from pecan.secure import secure
from microformats2 import validate
from datetime import datetime
from copy import deepcopy

from .. import slug
from .. import storage
from .. import media
from .. import auth

import cgi
import json
import jsonschema
import requests


class ForceJSONContentTypeHook(PecanHook):
    '''
    Some Micropub clients aren't very smart about setting Content-Type headers.
    Force a proper `application/json` header on their behalf.
    '''

    def on_route(self, state):
        if not state.request.headers.get('Content-Type'):
            state.request.headers['Content-Type'] = 'application/json'
        return PecanHook.on_route(self, state)


class MicropubController:

    __hooks__ = [ForceJSONContentTypeHook()]


    @expose('json', generic=True)
    def index(self, *args, **kwargs):
        '''
        HTTP GET /micropub

        Handle queries for `config`, `syndicate-to`, and `source`.
        '''

        if kwargs.get('q') == 'config':
            return {
                'media-endpoint': conf.app.public_url + '/media'
            }

        if kwargs.get('q') == 'syndicate-to':
            return {
                'syndicate-to': []
            }

        if kwargs.get('q') == 'source':
            mf2 = storage.get_by_permalink(kwargs['url'])

            copy = deepcopy(mf2)

            if 'properties[]' in kwargs:
                for key in mf2['properties'].keys():
                    if key not in kwargs['properties[]']:
                        del copy['properties'][key]

            return copy

        return dict()


    @secure(auth.check_permissions)
    @index.when(method='POST')
    @expose('json')
    def publish(self, *args, **kwargs):
        '''
        HTTP POST /micropub

        Handle all Micropub actions, including:

        * create
        * update
        * delete
        * undelete

        Data is stored in a JSON database called TinyDB.
        '''

        # first, get our JSON payload set up
        payload = {}

        # in the event that the POST data is urlencoded form data...
        if request.headers['Content-Type'] == 'application/x-www-form-urlencoded':
            # if an action is specified, that means we don't need to decode any
            # MF2 data, and can just use the passed-in parameters
            if request.params.get('action'):
                payload = request.params

            # otherwise, decode the data into a standard MF2 JSON structure
            else:
                payload = self.decode_mf2(request.POST)

        # if its a multipart request, make sure to handle that properly
        elif request.headers['Content-Type'].startswith('multipart/form-data'):
            # multipart means that one of the bits is a media upload
            payload = self.decode_mf2(request.POST, media_upload=True)

        # hey, its JSON data, which means we have MF2 data we can validate later
        elif request.headers['Content-Type'] == 'application/json':
            payload = request.json

        # if all of these conditions fail, reject the request
        else:
            abort(400, 'Invalid request data')

        # handle update, delete, and undelete actions
        if payload.get('action') == 'update':
            if self.update_post(payload):
                response.status = 204
                return dict()
            abort(400, 'Invalid request data')
        elif payload.get('action') == 'delete':
            if self.delete_post(payload):
                response.status = 204
                return dict()
            abort(400, 'Invalid request data')
        elif payload.get('action') == 'undelete':
            if self.undelete_post(payload):
                response.status = 204
                return dict()
            abort(400, 'Invalid request data')

        # handle create requests... first, if there is no publish date,
        # synthesize one
        if 'published' not in payload['properties']:
            payload['properties']['published'] = [
                datetime.utcnow().isoformat()
            ]

        # if an author property hasn't been provided, synthesize one
        if 'author' not in payload['properties']:
            payload['properties']['author'] = [{
                'type': ['h-card'],
                'properties': {
                    'name': [ conf.author.name ],
                    'url': [ conf.author.url ],
                    'photo': [ conf.author.photo ]
                }
            }]

        # validate that the payload is valid MF2 JSON, matching some known
        # vocabulary
        invalid = self.validate_content(payload)
        if invalid:
            # TODO: just use standard responses here...
            response.status = 400
            response.headers['Content-Type'] = 'application/json'
            response.text = json.dumps({'validation_error': str(invalid)})
            return

        # generate a slug for this post
        page_slug = slug.generate_slug(payload)
        payload['properties']['url'] = [conf.app.public_url + '/view/entry/' + page_slug]

        # store the raw content in our database
        storage.store(payload)

        # redirect to the rendered content
        response.status = '201'
        response.headers['Location'] = payload['properties']['url'][0]


    def update_post(self, payload):
        '''
        Handle updating a post.
        '''

        # find the document
        doc = storage.get_by_permalink(payload['url'])
        if not doc:
            abort(404)

        # handle replacement of properties
        if 'replace' in payload:
            if not isinstance(payload['replace'], dict):
                abort(400)
            for key, value in payload['replace'].items():
                doc['properties'][key] = value

        # handle addition of properties
        elif 'add' in payload:
            for key, value in payload['add'].items():
                for item in value:
                    doc['properties'].setdefault(key, []).append(item)

        # handle deletion of properties
        elif 'delete' in payload:
            if isinstance(payload['delete'], dict):
                for key, value in payload['delete'].items():
                    for item in value:
                        doc['properties'].setdefault(key, []).remove(item)
            elif isinstance(payload['delete'], list):
                for key in payload['delete']:
                    del doc['properties'][key]

        # update the record in the data store
        storage.update(payload['url'], doc)

        return True


    def delete_post(self, payload):
        '''
        Handle (soft) deleting a post.
        '''

        # find the document
        doc = storage.get_by_permalink(payload['url'])
        if not doc:
            abort(404)

        # perform a soft-delete on the record
        storage.delete(payload['url'], soft=True)

        return True


    def undelete_post(self, payload):
        '''
        Handle un-deleting a post.
        '''

        # find the document
        doc = storage.get_by_permalink(payload['url'], hidden=True)
        if not doc:
            abort(404)

        # soft-undelete the record
        storage.undelete(payload['url'])

        return True


    def decode_mf2(self, post, media_upload=False):
        '''
        The client has provided formencoded data, like an animal.
        Decode it into standard MF2 JSON.
        '''

        mf2 = {}
        mf2['type'] = [ 'h-' + post.get('h', 'entry')]
        mf2['properties'] = {}
        mf2['properties']['content'] = [
            post.get('content', '')
        ]

        for key in post.keys():
            if key in ('h', 'content', 'access_token'):
                continue

            # if its a multipart upload, handle it
            if isinstance(post[key], cgi.FieldStorage):
                if not media_upload:
                    continue

                permalink = media.upload_file(post[key].file, post[key].filename)
                mf2['properties'].setdefault(key.replace('[]', ''), []).append(permalink)

                continue

            mf2['properties'][key.replace('[]', '')] = post.getall(key)

        return mf2


    def validate_content(self, mf2):
        '''
        Validate the MF2 JSON data using JSON Schema.
        '''

        try:
            validate(mf2)
        except jsonschema.ValidationError as e:
            return e
        except:
            return 'Invalid Request'
