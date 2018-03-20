from pecan import make_app
from pecan.hooks import TransactionHook

from . import storage


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
            )
        ],
        **app_conf
    )
