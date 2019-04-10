import threading

import websocket


class NetworkHandler:
    def __init__(self):
        self.listener = None
        self.networkSocket = websocket.WebSocketApp(
            "ws://minesweeper.griffgriffgames.com/websocket",
            on_message=self.on_message,
            on_error=self.on_error,
            on_open=self.on_open,
            on_close=self.on_close)
        # ws.on_open = on_open
        wst = threading.Thread(target=self.networkSocket.run_forever)
        wst.daemon = True
        wst.start()

    def on_message(self, message):
        if self.listener is not None:
            self.listener.on_message(message)

    def on_error(self, error):
        if self.listener is not None:
            self.listener.on_error(error)

    def on_close(self):
        if self.listener is not None:
            self.listener.on_connection_closed()

    def on_open(self):
        if self.listener is not None:
            self.listener.on_connection_opened()

    def set_listener(self, listener):
        self.listener = listener
