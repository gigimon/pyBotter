import re
import logging
from lxml import etree

from base import BaseUrlParserHandler

LOG = logging.getLogger('plugins:twitter')

class Twitter(BaseUrlParserHandler):

    parse_re = re.compile(r'((?:http|https)://twitter.com/.+/status/\d+)')
    filter_url = 'twitter.com'

    def worker(self, message):
        urls = self.parse_re.findall(message['message'])
        messages = []
        for url in urls:
            tree = self.create_html_tree(url)
            tweet = tree.xpath("//p[contains(@class, 'tweet-text')]")[0]
            tweet_name = '@'+tree.xpath("//span[contains(@class, 'username js-action-profile-name')]/b")[0].text
            realname = tree.xpath("//strong[contains(@class, 'fullname js-action-profile-name')]")[0].text
            etree.strip_tags(tweet, 's','a','span','b')
            tweet_parts = self.stringify_children(tweet)
            tweet_text = "\00310%s (%s): \00314%s\003" % (tweet_name, realname, tweet_parts.strip())
            LOG.info('Twitter message (%s): %s' % (url, tweet_text))
            messages.append({'receiver': message['receiver'],
                            'message': tweet_text.encode('latin1')})
        return messages

