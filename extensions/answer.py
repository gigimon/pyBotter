from base import BaseFirstWordHandler

class Answer(BaseFirstWordHandler):
    keywords = ['!answer']

    def worker(self, message):
        m = {'receiver': message['receiver'],
             'message': ' '.join(message['message'].split()[1:])}
        return m
