import gevent
from gevent.greenlet import Greenlet

class BaseFirstWordHandler(object):
    keywords = []

    def __init__(self, loader):
        self._loader = loader

    def run(self, message):
        for kw in self.keywords:
            if message['message'].startswith(kw):
                gevent.spawn(self._run, message)

    def _run(self, message):
        pass


class BaseMessageHandler(object):

    def __init__(self, loader):
        self._loader = loader

    def run(self, message):
        Greenlet.spawn(self._run, message)

    def _run(self, message):
        pass