from base import BaseFirstWordHandler

class Answer(BaseFirstWordHandler):
    keywords = ['!answer']

    def _run(self, message):
        m = {'receiver': message['receiver'],
             'message': ' '.join(message['message'].split()[1:])}
        self._loader.return_to_server(m)
