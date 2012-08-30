import re
import urllib2
from lxml import etree
from lxml.etree import tostring
from itertools import chain

from base import BaseMessageHandler

class Twitter(BaseMessageHandler):

    parse_re = re.compile(r'((?:http|https)://twitter.com/.+/status/\d+)')

    def filter(self, message):
        if 'twitter.com' in message['message']:
            return True
        return False

    def worker(self, message):
        def stringify_children(node):
            from lxml.etree import tostring
            from itertools import chain
            parts = ([node.text] +
                     list(chain(*([c.text, tostring(c), c.tail] for c in node.getchildren()))) +
                     [node.tail])
            # filter removes possible Nones in texts and tails
            return ''.join(filter(None, parts))
        urls = self.parse_re.findall(message['message'])
        messages = []
        for url in urls:
            p = urllib2.urlopen(url).read()
            tree = etree.HTML(p)
            tweet = tree.xpath("//p[contains(@class, 'tweet-text')]")[0]
            tweet_name = '@'+tree.xpath("//span[contains(@class, 'username js-action-profile-name')]/b")[0].text
            realname = tree.xpath("//strong[contains(@class, 'fullname js-action-profile-name')]")[0].text
            etree.strip_tags(tweet, 's','a','span','b')
            tweet_parts = stringify_children(tweet)
            tweet_text = "\00304%s\00301 (%s): %s" % (tweet_name, realname, tweet_parts.strip())
            messages.append({'receiver': message['receiver'],
                            'message': tweet_text.encode('latin1')})
        return messages

