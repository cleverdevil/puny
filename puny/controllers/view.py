from pecan import conf, expose, abort, redirect, request, response

from .. import storage


class DocumentController:

    def __init__(self, doc):
        self.doc = doc

    @expose(template='single.html')
    def index(self):
        return self.doc


class ContentController:

    @expose()
    def _lookup(self, slug, *remainder):
        doc = storage.get_by_permalink(conf.app.public_url + '/view/entry/' + slug)
        if doc is None:
            abort(404)

        return DocumentController(doc), remainder


class ViewController:
    entry = ContentController()

    @expose(template='timeline.html')
    def index(self, limit=20, offset=0):
        entries = storage.find(limit=limit, offset=offset)

        return dict(entries=entries)
