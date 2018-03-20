from pecan import expose, request, response, abort, conf
from pecan.secure import secure

from .. import auth
from .. import media

import requests


class MediaController:

    @expose(generic=True)
    def index(self, *args, **kwargs):
        pass

    @secure(auth.check_permissions)
    @index.when(method='POST')
    def publish(self, *args, **kwargs):
        if 'file' not in request.params:
            abort(400, 'Invalid request: no files uploaded.')

        upload = request.params['file']

        permalink = media.upload_file(upload.file, upload.filename)

        response.status = '201'
        response.headers['Location'] = permalink
