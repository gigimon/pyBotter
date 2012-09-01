import re
import urllib2
import logging
from lxml import etree
from lxml.etree import tostring
from itertools import chain

from base import BaseMessageHandler

LOG = logging.getLogger('plugins:open_vk')

class Open_VK(BaseMessageHandler):

    parse_re = re.compile(r'(http://vk.com/wall[_\d]+)')

    def filter(self, message):
        if 'vk.com' in message['message']:
            return True
        return False

    def worker(self, message):
        def stringify_children(node):
            parts = ([node.text] +
                     list(chain(*([c.text, tostring(c), c.tail] for c in node.getchildren()))) +
                     [node.tail])
            return ''.join(filter(None, parts))
        urls = self.parse_re.findall(message['message'])
        messages = []
        for url in urls:
            LOG.info('Get text from:\'%s\'' % url)
            p = urllib2.urlopen(url).read()
            tree = etree.HTML(p)
            content = tree.xpath("//div[contains(@class, 'wall_post_text')]")[0]
            user_name = tree.xpath("//a[contains(@class, 'fw_post_author')]")[0].text
            etree.strip_tags(content, 's','a','span','b', 'br')
            message_parts = stringify_children(content)
            all_text = "\00304%s\00301: %s" % (user_name, message_parts.strip())
            messages.append({'receiver': message['receiver'],
                         'message': all_text.encode('utf8')})
        return messages