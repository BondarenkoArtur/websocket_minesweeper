class WSListener:
    def on_message(self, message):
        raise NotImplementedError("Subclass should implement on_message")
