class UpdateListener:
    def __init__(self, ui):
        pass

    def on_error(self, error):
        raise NotImplementedError

    def on_message(self, message):
        raise NotImplementedError

    def on_connection_opened(self):
        raise NotImplementedError

    def on_connection_closed(self):
        raise NotImplementedError
