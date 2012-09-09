import re
import logging
from lxml import etree


from base import BaseUrlParserHandler

LOG = logging.getLogger('plugins:open_vk')

class Open_VK(BaseUrlParserHandler):

    parse_re = re.compile(r'(http://vk.com/wall[_\d]+)')
    filter_url = 'vk.com'

    def worker(self, message):
        urls = self.parse_re.findall(message['message'])
        messages = []
        for url in urls:
            tree = self.create_html_tree(url)
            content = tree.xpath("//div[contains(@class, 'wall_post_text')]")[0]
            user_name = tree.xpath("//a[contains(@class, 'fw_post_author')]")[0].text
            etree.strip_tags(content, 's','a','span','b', 'br')
            message_parts = self.stringify_children(content)
            all_text = self.colorize(user_name, message_parts.strip())
            LOG.info('VK.com message (%s): %s' % (url, all_text))
            messages.append({'receiver': message['receiver'],
                         'message': all_text.encode('utf8')})
        return messages