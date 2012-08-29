import os
import sys
import logging

import gevent

from base import BaseFirstWordHandler, BaseMessageHandler

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

LOG = logging.getLogger('Loader')

class Loader(object):
    def __init__(self, bus):
        self._plugins = []
        self.bus = bus

    def load_plugins(self):
        for m in os.listdir('extensions/'):
            if not m.endswith('.pyc') and not m.startswith('__') and not m in ['base.py']:
                name = m.split('.')[0]
                module = __import__(name, globals(), locals())
                for cls in dir(module):
                    c = getattr(module, cls)
                    try:
                        if (issubclass(c, BaseFirstWordHandler) or issubclass(c, BaseMessageHandler)) and not c in [BaseFirstWordHandler, BaseMessageHandler]:
                            self.add_plugin(c(self))
                    except TypeError:
                        continue

    def add_plugin(self, plugin_instance):
        LOG.info('Add new plugin: %s' % plugin_instance)
        for plugin in self._plugins:
            if type(plugin_instance) == type(plugin):
                break
        else:
            self._plugins.append(plugin_instance)

    def return_to_server(self, message):
        self.bus.send_out_message(message)

    def work(self):
        def check_messages():
            while True:
                message = self.bus.get_in_message()
                if message:
                    for plugin in self._plugins:
                        plugin.run(message)
                else:
                    gevent.sleep()
        self._worker = gevent.spawn(check_messages)