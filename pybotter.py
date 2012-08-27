import uuid
import logging

import gevent
from gevent import socket

import conf

LOG = logging.getLogger('Botter')


class Botter(object):
    def __init__(self, init_channels=None):
        self._conn = None
        if init_channels is None:
            self._init_channels = []
        else:
            self._init_channels = init_channels

    def connect(self, server, port, username, realname=None):
        LOG.info('Connect to %s:%s' % (server, port))
        self._conn = socket.create_connection((server, port))
        if realname == None:
            realname = username
        self._conn.send("""PASS {uniquepass}\r\n
        NICK {username}\r\n
        USER {username} testbot testbot :{realname}\r\n""".format(uniquepass=uuid.uuid1().hex, username=username, realname=realname))

    def pong(self, msg):
        answer = msg.strip().split(':')[1]
        self._conn.send('PONG %s\r\n' % answer)
        LOG.debug('Send PONG to server: %s' % answer)

    def _parse_message(self, buf):
        LOG.info('Start message parsing')
        for msg in buf.split('\r\n'):
            msg = msg.strip()
            if not msg:
                continue
            LOG.info('Parse: %s' % msg)
            if msg.startswith('PING'):
                self.pong(msg)
                continue
            msg_opts = msg.split()
            sender = msg_opts[0][1:].split('!')[0]
            receiver = msg_opts[2]
            msg_type = msg_opts[1]
            message = ' '.join(msg_opts[3:])[1:]
            if msg_type == 'NOTICE' and receiver == 'AUTH' and message.startswith('*** You connected'):
                for chan in self._init_channels:
                    self.join_channel(chan)
            if sender == 'gigimon':
                self._conn.send('%s\r\n' % message)

    def send_message(self, receiver, message):
        LOG.info('Send "%s" to "%s"' % (message, receiver))
        self._conn.send('PRIVMSG %s :%s\r\n' % (receiver, message))

    def join_channel(self, channel):
        LOG.info('Join to channel %s' % channel)
        if not channel.startswith('#'):
            channel = '#' + channel
        if len(channel.split(':')) > 1:
            channel, password = channel.split(':')
            self._conn.send('JOIN %s %s\r\n' % (channel, password))
        self._conn.send('JOIN %s\r\n' % channel)

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
    bot = Botter(conf.config['channels'])
    bot.connect(conf.config['server']['host'],
                conf.config['server']['port'],
                conf.config['user']['nickname'],
                conf.config['user']['realname']
    )
    bot.work()