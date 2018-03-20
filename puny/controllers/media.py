from pecan import expose, request, response, abort, conf
from pecan.secure import secure

from .. import auth
from .. import media

import requests


class MediaController:

    @secure(auth.check_permissions)
    @expose(content_type='multipart/form-data')
    @expose('json')
    def index(self, *args, **kwargs):
        if request.method != 'POST':
            return

        if 'file' not in request.params:
            abort(400, 'Invalid request: no files uploaded.')

        upload = request.params['file']

        permalink = media.upload_file(upload.file, upload.filename)

        response.status = '201'
        response.headers['Location'] = permalink
