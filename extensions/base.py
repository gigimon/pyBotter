import gevent
from gevent.greenlet import Greenlet


class BaseHandler(object):
    """Main class for all handler"""
    def __init__(self, loader):
        self._loader = loader

    def run(self, message):
        if self.filter(message):
            g = gevent.spawn(self.worker, message)
            g.link_value(self.send_result)

    def worker(self, message):
        return

    def filter(self, message):
        return True

    def send_result(self, greenlet):
        if greenlet.value:
            self._loader.return_to_server(greenlet.value)

class BaseFirstWordHandler(BaseHandler):
    keywords = []

    def filter(self, message):
        for kw in self.keywords:
            if message['message'].startswith(kw):
                return True
        return False

class BaseMessageHandler(BaseHandler):
    pass