from random import randint
from base import BaseFirstWordHandler

class Decidey(BaseFirstWordHandler):
    keywords = ['!decide']
    help_string = 'usage: !decide variant1, variant2, ... variantN'

    def worker(self, message):
        data = message['message'].split()[1:]
        data = ' '.join([item for item in data])
        if not data:
            m = {'receiver': message['receiver'],
             'message': self.help_string}
        else:
            variants = data.split(',')
            variants = [item.strip() for item in variants]
            variants = filter(str, variants)
            if len(variants) > 1:
                index = randint(0, len(variants) - 1)
                choice = variants[index]
            else:
                choice = ''
            m = {'receiver': message['receiver'],
             'message': 'My choice is %s' % choice if choice else self.help_string}
        return m
