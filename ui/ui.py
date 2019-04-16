class UIHandler:
    def get_listener(self):
        raise NotImplementedError("Subclass should implement get_listener")

    def is_running(self):
        raise NotImplementedError("Subclass should implement is_running")

    def update_ui(self):
        raise NotImplementedError("Subclass should implement update_ui")
