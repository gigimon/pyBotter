from conf import config

class BotAdmin(object):
    def __init__(self):
        self.username = config['admin']['username']
        self.password = config['admin']['password']
        self.ident = None
        self._authorized = False

    def check_password(self, password):
        return self.password == password

    def authorized(self, message):
        if self._authorized:
            if message['sender'] == self.username and message['user_ident'] == self.ident:
                return True
        else:
            return False

    def authorize(self, message):
        if not self.authorized(message):
            if message['sender'] == self.username and message['message'].startswith('!answer'):
                if self.check_password(message['message'].split()[1]):
                    self.ident = message['user_ident']
                    self._authorized = True
                    return {'receiver': message['sender'], 'message': 'Ты авторизован как администратор'}
                else:
                    return {'receiver': message['sender'], 'message': 'Пароль не подошел'}
            else:
                return {'receiver': message['sender'], 'message': 'Ты не авторизован, используй "!auth пароль"'}
        elif self.authorized(message):
            return {'receiver': message['sender'], 'message': 'Ты уже авторизован'}

