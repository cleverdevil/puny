from pecan import make_app
from pecan.hooks import TransactionHook, PecanHook

from . import storage


class ForceJSONContentTypeHook(PecanHook):
    '''
    Some Micropub clients aren't very smart about setting Content-Type headers.
    Force a proper `application/json` header on their behalf.
    '''

    def on_route(self, state):
        ct = state.request.headers.get('Content-Type')

        if state.request.path == '/micropub':
            if not ct in ('application/json', 'application/x-www-form-urlencoded'):
                if not ct.startswith('multipart/form-data'):
                    state.request.headers['Content-Type'] = 'application/json'

        return PecanHook.on_route(self, state)



def setup_app(config):

    app_conf = dict(config.app)

    return make_app(
        app_conf.pop('root'),
        logging=getattr(config, 'logging', {}),
        hooks= [
            TransactionHook(
                storage.start,
                storage.start_read_only,
                storage.commit,
                storage.rollback,
                storage.clear
            ),
            ForceJSONContentTypeHook()
        ],
        **app_conf
    )
