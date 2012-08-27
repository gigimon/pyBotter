import logging
import ConfigParser

import gevent
from gevent import socket

import conf

LOG = logging.getLogger('Botter')


class Botter(object):
    def __init__(self):
        self._conn = None

    def connect(self, server, port, username):
        LOG.info('Connect to %s:%s' % (server, port))
        self._conn = socket.create_connection((server, port))
        self._conn.send('PASS testpass\r\nNICK testbot\r\nUSER testbot test test :realname\r\n')

    def pong(self, msg):
        answer = msg.strip().split(':')[1]
        self._conn.send('PONG %s\r\n' % answer)
        LOG.debug('Send PONG to server: %s' % answer)

    def _parse_message(self, buf):
        LOG.info('Start message parsing')
        for msg in buf.split('\r\n'):
            if not msg.strip():
                continue
            LOG.info('Parse: %s' % msg)
            if msg.strip().startswith('PING'):
                self.pong(msg)
                continue
            msg_opts = msg.split()
            sender = msg_opts[0][1:].split('!')[0]
            receiver = msg_opts[2]
            msg_type = msg_opts[1]
            message = ' '.join(msg_opts[3:])[1:]
            if sender == 'gigimon':
                self._conn.send('%s\r\n' % ' '.join(message.split()[1:]))

    def send_message(self, receiver, message):
        LOG.info('Send "%s" to "%s"' % (message, receiver))
        self._conn.send('PRIVMSG %s :%s\r\n' % (receiver, message))

    def work(self):
        buf = ''
        while True:
            msg = self._conn.recv(512)
            LOG.debug('Get from server: %s' % msg)
            buf += msg
            if len(msg) < 512 and msg.endswith('\r\n'):
                self._parse_message(buf)
                buf = ''


if __name__ == '__main__':
    bot = Botter()
    bot.connect('irc.nnm.ru', 5557, 'superbot')
    bot.work()