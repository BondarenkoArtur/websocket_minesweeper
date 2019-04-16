class Data:
    def __init__(self):
        self.global_data = {}
        self.message_array = {}

    def set_global_data(self, key, data):
        if key in self.global_data:
            self.global_data[key].update(data)
        else:
            self.global_data[key] = data

    def get_global_data(self, key):
        if key in self.global_data:
            return self.global_data[key]
        else:
            return None

    def get_msg(self, key):
        if key in self.message_array:
            return self.message_array[key]
        else:
            return None

    def add_msg(self, key, data):
        self.message_array[key] = data
