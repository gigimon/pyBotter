from gevent.queue import Queue

class Bus(object):
    def __init__(self):
        self._out_queue = Queue()
        self._in_queue = Queue()

    def get_out_message(self):
        """Get message from out_queue (for server)"""
        if self._out_queue.empty():
            return None
        else:
            return self._out_queue.get_nowait()

    def send_in_message(self, message):
        """Send message to plugins"""
        if isinstance(message, list):
            for m in message:
                self._in_queue.put(m)
        else:
            self._in_queue.put(message)

    def exist_out_messages(self):
        return not self._out_queue.empty()

    def get_in_message(self):
        """Get message from in_queue (for plugins)"""
        if self._in_queue.empty():
            return None
        else:
            return self._in_queue.get_nowait()

    def send_out_message(self, message):
        """Method for plugins to send message to server"""
        if isinstance(message, list):
            for m in message:
                self._out_queue.put(m)
        else:
            self._out_queue.put(message)

    def exist_in_messages(self):
        return not self._in_queue.empty()