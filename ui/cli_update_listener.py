from ui.ui_update_listener import UpdateListener


class CLIUpdateListener(UpdateListener):
    def __init__(self, ui):
        super().__init__(ui)
        self.ui = ui

    def on_connection_opened(self):
        self.ui.print("Connection opened")

    def on_error(self, error):
        self.ui.print("E:", error)

    def on_message(self, message):
        self.ui.print("R:", message)

    def on_send(self, message):
        self.ui.print("S:", message)

    def on_connection_closed(self):
        self.ui.print("Connection closed")
