# coding=utf-8
import re

import umysql
import logging

from base import BaseMessageHandler
from conf import config

LOG = logging.getLogger('UrlSaver')

class UrlSaver(BaseMessageHandler):

    url_re = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', re.U)
    db = umysql.Connection()

    def filter(self, message):
        if self.url_re.findall(message['message']):
            return True

        if message['message'].strip().split() and message['message'].strip().split()[0] in ['!lurls', '!furls']:
            return True
        return False

    def worker(self, message):
        if not self.db.is_connected():
            LOG.debug('Connect to database...')
            self.db.connect(config['plugins']['UrlSaver']['host'], 3306,
                config['plugins']['UrlSaver']['username'],
                config['plugins']['UrlSaver']['password'],
                config['plugins']['UrlSaver']['database'], True
            )
        urls = self.url_re.findall(message['message'])
        for url in urls:
            LOG.debug('Insert url %s' % url)
            self.db.query('INSERT INTO url_saver (url, sender, date) VALUES ("%s", "%s", NOW())' % (url, message['sender']))
        words = message['message'].strip().split()
        if words:
            first_word = words[0]
            LOG.debug('First word: %s' % first_word)
        else:
            first_word = ''
        if first_word == '!lurls':
            LOG.debug('Send last 10 urls')
            messages = []
            res = self.db.query('SELECT sender, url, date FROM url_saver ORDER BY date DESC LIMIT 10')
            for row in res.rows:
                messages.append({'receiver': message['sender'], 'message': '%s %s: %s' % (row[2].strftime('%d.%m.%y %H:%M'),
                                                                                            row[0], row[1],)})
            return messages
        elif first_word == '!furls':
            if len(words) > 1:
                search_word = words[1]
                LOG.debug('Find %s' % search_word)
            else:
                return {'receiver': message['receiver'], 'message': 'Надо так: !furls <что_ищем>'}
            res = self.db.query("""SELECT sender, url, date FROM url_saver
                                WHERE url LIKE "%{0}%" OR sender LIKE "%{0}%"
                                ORDER BY date DESC
                                LIMIT 10""".format(search_word))
            if res.rows:
                messages = []
                for row in res.rows:
                    messages.append({'receiver': message['sender'], 'message': '%s %s: %s' % (row[2].strftime('%d.%m.%y %H:%M'),
                                                                                                row[0], row[1],)})
                return messages
            else:
                return {'receiver': message['receiver'], 'message': 'Ничего не нашел :('}
