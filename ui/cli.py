from ui.cli_update_listener import CLIUpdateListener
from ui.ui import UIHandler


class CLIHandler(UIHandler):
    def __init__(self):
        self.listener = CLIUpdateListener(self)

    def get_listener(self):
        return self.listener

    @staticmethod
    def print(*args):
        print(*args)

    def is_running(self):
        return True
