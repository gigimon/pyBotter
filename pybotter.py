import uuid
import logging

from gevent import monkey; monkey.patch_all()
import gevent
from gevent import socket

import conf
from bus import Bus
from extensions import Loader

LOG = logging.getLogger('Botter')

class Botter(object):
    def __init__(self, username, username_password=None, realname=None, init_channels=None):
        self._conn = None
        self._write_conn = None
        self._read_conn = None

        self.username = username
        self.username_password = username_password
        if not realname:
            self.realname = username
        else:
            self.realname = realname
        self.bus = Bus()
        self.plugins = Loader(self.bus)
        self.plugins.load_plugins()

        self.joined = False

        if init_channels is None:
            self._init_channels = []
        else:
            self._init_channels = init_channels

    def connect(self, server, port):
        LOG.info('Connect to %s:%s' % (server, port))
        self._con_opts = (server, port)
        self._conn = socket.create_connection((server, port))
        self._conn.send("""PASS {uniquepass}\r\n
        NICK {username}\r\n
        USER {username} testbot testbot :{realname}\r\n""".format(uniquepass=uuid.uuid1().hex,
            username=self.username,
            realname=self.realname))
        self._write_conn = self._conn.dup()
        self._read_conn = self._conn.dup()

    def pong(self, msg):
        answer = msg.strip().split(':')[1]
        self._write_conn.send('PONG %s\r\n' % answer)

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
            if 'ERROR :Closing Link:' in msg:
                self.connect(self._con_opts[0], self._con_opts[1])
                return []
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
            if msg_type == 'NOTICE' and sender == 'NickServ' and 'NickServ IDENTIFY' in message:
                self.authorize()
                continue
            messages.append({'sender': sender,
                             'receiver': receiver,
                             'msg_type': msg_type,
                             'message': message,
                             'user_ident': user_ident})
        return messages

    def authorize(self):
        LOG.info('Authorize in nickserv')
        if self.username_password:
            self.bus.send_out_message({'receiver':'NickServ',
                                       'message': 'identify %s' % self.username_password})

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
        self.joined = True
        if not channel.startswith('#'):
            channel = '#' + channel
        if len(channel.split(':')) > 1:
            channel, password = channel.split(':')
            self._write_conn.send('JOIN %s %s\r\n' % (channel, password))
        else:
            self._write_conn.send('JOIN %s\r\n' % channel)

    def work(self):
        """Start Loader check bus to input messages"""
        receive = gevent.spawn(self._start_recv)
        sender = gevent.spawn(self._start_send)
        while not self.joined:
            gevent.sleep(1)
        self.plugins.work()
        gevent.joinall([ receive, sender ])

    def _start_recv(self):
        buf = ''
        while True:
            try:
                msg = self._read_conn.recv(512)
            except socket.error, e:
                LOG.error('Can\'t send message: %s' % e)
                if 'Broken pipe' in e:
                    LOG.info('Reconnect to server')
                    self.connect(self._con_opts[0], self._con_opts[1])
            buf += msg
            if len(msg) < 512 and msg.endswith('\r\n'):
                messages = self._parse_message(buf)
                buf = ''
                if messages:
                    self.bus.send_in_message(messages)
            gevent.sleep(0.1)

    def _start_send(self):
        while True:
            while self.bus.exist_out_messages():
                LOG.debug("Send to server message")
                try:
                    self.send_message(self.bus.get_out_message())
                except socket.error, e:
                    LOG.error('Can\'t send message: %s' % e)
                    if 'Broken pipe' in e:
                        LOG.info('Reconnect to server')
                        self.connect(self._con_opts[0], self._con_opts[1])
            gevent.sleep(0.1)


def main():
    bot = Botter(conf.config['user']['nickname'],
                username_password=conf.config['user']['password'],
                realname=conf.config['user']['realname'],
                init_channels=conf.config['channels'],
            )
    bot.connect(conf.config['server']['host'],
        conf.config['server']['port'],
            )
    bot.work()

if __name__ == '__main__':
    main()