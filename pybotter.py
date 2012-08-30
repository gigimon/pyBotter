import os
import sys

import uuid
import logging

import gevent
from gevent import socket
from gevent import monkey; monkey.patch_all()

import conf
from bus import Bus
from extensions import Loader

LOG = logging.getLogger('Botter')

class Botter(object):
    def __init__(self, init_channels=None):
        self._conn = None
        self._write_conn = None
        self._read_conn = None

        self.bus = Bus()
        self.plugins = Loader(self.bus)
        self.plugins.load_plugins()

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
        self._write_conn = self._conn.dup()
        self._read_conn = self._conn.dup()

    def pong(self, msg):
        answer = msg.strip().split(':')[1]
        self._write_conn.send('PONG %s\r\n' % answer)
        LOG.debug('Send PONG to server: %s' % answer)

    def _parse_message(self, buf):
        LOG.info('Start message parsing')
        messages = []
        for msg in buf.split('\r\n'):
            msg = msg.strip()
            if not msg:
                continue
            LOG.info('Parse: %s' % msg)
            if msg.startswith('PING'):
                self.pong(msg)
                continue
            msg_opts = msg.split()
            user_opts = msg_opts[0][1:].split('!')
            if len(user_opts) > 1:
                sender, user_ident = user_opts[0], user_opts[1]
            else:
                sender, user_ident = user_opts[0], None
            receiver = msg_opts[2]
            msg_type = msg_opts[1]
            message = ' '.join(msg_opts[3:])[1:]
            if msg_type == 'NOTICE' and receiver == 'AUTH' and message.startswith('*** You connected'):
                for chan in self._init_channels:
                    self.join_channel(chan)
            messages.append({'sender': sender,
                             'receiver': receiver,
                             'msg_type': msg_type,
                             'message': message,
                             'user_ident': user_ident})
        return messages

    def send_message(self, message):
        if isinstance(message, list):
            for m in message:
                LOG.info('Send "%s" to "%s"' % (m['message'], m['receiver']))
                self._write_conn.send('PRIVMSG %s :%s\r\n' % (m['receiver'], m['message']))
        else:
            LOG.info('Send "%s" to "%s"' % (message['message'], message['receiver']))
            self._write_conn.send('PRIVMSG %s :%s\r\n' % (message['receiver'], message['message']))

    def join_channel(self, channel):
        LOG.info('Join to channel %s' % channel)
        if not channel.startswith('#'):
            channel = '#' + channel
        if len(channel.split(':')) > 1:
            channel, password = channel.split(':')
            self._write_conn.send('JOIN %s %s\r\n' % (channel, password))
        self._write_conn.send('JOIN %s\r\n' % channel)

    def work(self):
        """Start Loader check bus to input messages"""
        self.plugins.work()
        gevent.joinall([
            gevent.spawn(self._start_recv),
            gevent.spawn(self._start_send),
            ])

    def _start_recv(self):
        buf = ''
        while True:
            msg = self._read_conn.recv(512)
            LOG.debug('Get from server: %s' % msg)
            buf += msg
            if len(msg) < 512 and msg.endswith('\r\n'):
                messages = self._parse_message(buf)
                buf = ''
                self.bus.send_in_message(messages)

    def _start_send(self):
        while True:
            while self.bus.exist_out_messages():
                LOG.debug("Send to server message")
                self.send_message(self.bus.get_out_message())
            gevent.sleep()

if __name__ == '__main__':
    bot = Botter(conf.config['channels'])
    bot.connect(conf.config['server']['host'],
                conf.config['server']['port'],
                conf.config['user']['nickname'],
                conf.config['user']['realname']
    )
    bot.work()