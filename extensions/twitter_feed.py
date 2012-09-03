from base import BaseAlwaysRunningHandler

import gevent
import logging

import tweepy

from conf import config

LOG = logging.getLogger('TwitterFeed')

class TwitterFeed(BaseAlwaysRunningHandler):
    def worker(self):
        auth = tweepy.auth.OAuthHandler(config['plugins'][self.name]['consumer_key'],
            config['plugins'][self.name]['consumer_secret'],
        )
        auth.set_access_token(config['plugins'][self.name]['access_token_key'],
            config['plugins'][self.name]['access_token_secret'],
        )
        api = tweepy.API(auth)
        if api.test():
            last_id = 0
            channels = [chan.split(':')[0] for chan in config['channels']]
            while True:
                statuses = api.home_timeline()
                for status in reversed(statuses):
                    if status.id > last_id:
                        last_id = status.id
                        tweet_text = "\00304@%s\00301 (%s): %s" % (status.author.screen_name,
                                                                   status.author.name,
                                                                   status.text.strip())
                        for chan in channels:
                            self.send_message({'receiver': str(chan),
                                               'message': tweet_text.encode('utf8')})
                gevent.sleep(15)
        else:
            LOG.error('Can\'t read feed, because credentials is bad')
