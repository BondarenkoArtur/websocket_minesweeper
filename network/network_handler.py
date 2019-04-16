import threading

import websocket

from logic.main_worker import Worker
from network.message_parser import Parser

WEBSOCKET_URL = "ws://minesweeper.griffgriffgames.com/websocket"


class NetworkHandler:
    def __init__(self):
        self.ws_listeners = []
        self.ui_listener = None
        self.worker = None
        self.networkSocket = CustomSocket(WEBSOCKET_URL,
                                          on_message=self.on_message,
                                          on_send=self.on_send,
                                          on_error=self.on_error,
                                          on_open=self.on_open,
                                          on_close=self.on_close)
        wst = threading.Thread(target=self.networkSocket.run_forever)
        self.worker = Worker(self.networkSocket)
        self.parser = Parser(self.worker)
        wst.daemon = True
        wst.start()

    def on_message(self, message):
        try:
            if self.ui_listener is not None:
                self.ui_listener.on_message(message)
                self.parser.parse_message(message)
                for listener in self.ws_listeners:
                    listener.on_message(message)
        except Exception as e:
            self.on_error(str(e))

    def on_send(self, message):
        if self.ui_listener is not None:
            self.ui_listener.on_send(message)

    def on_error(self, error):
        if self.ui_listener is not None:
            self.ui_listener.on_error(error)

    def on_close(self):
        if self.ui_listener is not None:
            self.ui_listener.on_connection_closed()

    def on_open(self):
        if self.ui_listener is not None:
            self.ui_listener.on_connection_opened()

    def set_ui_listener(self, ui_listener):
        self.ui_listener = ui_listener

    def set_google_id(self, param):
        self.worker.set_google_id(param)

    def set_name(self, param):
        self.worker.set_name(param)


class CustomSocket(websocket.WebSocketApp):
    def __init__(self, url, header=None, on_open=None, on_message=None,
                 on_error=None, on_close=None, on_ping=None, on_pong=None,
                 on_cont_message=None, keep_running=True, get_mask_key=None,
                 cookie=None, subprotocols=None, on_data=None, on_send=None):
        self.on_send = on_send
        super().__init__(url, header, on_open, on_message, on_error, on_close,
                         on_ping, on_pong, on_cont_message, keep_running,
                         get_mask_key, cookie, subprotocols, on_data)

    def send(self, data, opcode=websocket.ABNF.OPCODE_TEXT):
        if self.on_send is not None:
            self.on_send(data)
        return super().send(data, opcode)
