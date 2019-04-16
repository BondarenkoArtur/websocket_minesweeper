class UpdateListener:
    def __init__(self, ui):
        pass

    def on_error(self, error):
        raise NotImplementedError("Subclass should implement on_error")

    def on_message(self, message):
        raise NotImplementedError("Subclass should implement on_message")

    def on_send(self, message):
        raise NotImplementedError("Subclass should implement on_send")

    def on_connection_opened(self):
        raise NotImplementedError("Subclass should implement "
                                  "on_connection_opened")

    def on_connection_closed(self):
        raise NotImplementedError("Subclass should implement "
                                  "on_connection_closed")
