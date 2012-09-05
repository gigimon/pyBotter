import re
import lxml
import gevent
import urllib2
import logging
from itertools import chain
from lxml import etree
from lxml.etree import tostring

LOG = logging.getLogger('BaseHandler')

class BaseHandler(object):
    """Main class for all handler"""
    def __init__(self, loader):
        self._loader = loader

    @property
    def name(self):
        return self.__class__.__name__

    def run(self, message):
        if self.filter(message):
            g = gevent.spawn(self.worker, message)
            g.link_value(self.send_result)

    def worker(self, message):
        """Greenlet worker"""
        raise NotImplementedError

    def filter(self, message):
        """This method run before worker for check message for this handler, must return Boolean"""
        raise NotImplementedError

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

    def filter(self, message):
        return True

class BaseUrlParserHandler(BaseHandler):
    parse_re = re.compile(r'')
    filter_url = ''

    def filter(self, message):
        if self.filter_url in message['message']:
            return True
        return False

    def stringify_children(self, node):
        parts = ([node.text] +
                 list(chain(*([c.text, tostring(c), c.tail] for c in node.getchildren()))) +
                 [node.tail])
        return ''.join(filter(None, parts))

    def create_html_tree(self, url):
        LOG.info('Get text from:\'%s\'' % url)
        p = urllib2.urlopen(url).read()
        tree = etree.HTML(p)
        return tree

class BaseAlwaysRunningHandler(BaseHandler):
    def run(self):
        g = gevent.spawn(self.worker)

    def worker(self):
        pass

    def send_message(self, message):
        self._loader.return_to_server(message)