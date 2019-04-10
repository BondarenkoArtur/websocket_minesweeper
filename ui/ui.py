class UIHandler:
    def get_listener(self):
        raise NotImplementedError

    def is_running(self):
        raise NotImplementedError

    def update_ui(self):
        raise NotImplementedError