from pecan import expose, request, response, abort, conf
from pecan.core import Response
from pecan.secure import secure

from webob.static import FileIter
from mimetypes import guess_type

from .. import auth
from .. import media

import requests


class MediaController:

    @secure(auth.check_permissions)
    @expose(content_type='multipart/form-data')
    @expose('json')
    def index(self, *args, **kwargs):
        if 'file' not in request.params:
            abort(400, 'Invalid request: no files uploaded.')

        upload = request.params['file']

        permalink = media.upload_file(upload.file, upload.filename)

        response.status = '201'
        response.headers['Location'] = permalink

    @expose()
    def _default(self, view, *remainder):
        body = media.get_file(request.path[12:])
        mime_type = guess_type(request.path[12:])[0]
        r = Response(
            content_type=mime_type
        )
        r.app_iter = FileIter(body)
        return r
