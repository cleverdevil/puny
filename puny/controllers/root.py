from pecan import expose, conf

from . import micropub
from . import media
from . import view


class RootController:
    micropub = micropub.MicropubController()
    media = media.MediaController()
    view = view.ViewController()

    @expose(template='index.html')
    def index(self):
        return dict()
