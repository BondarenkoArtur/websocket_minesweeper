class Data:
    def __init__(self):
        self.global_data = {}
        self.collection_data = {}
        self.message_array = {}
        self.subscriptions_array = {}

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

    def set_collection_data(self, key, key_id, data):
        if key not in self.collection_data:
            self.collection_data[key] = {}
        if key_id in self.collection_data[key]:
            self.collection_data[key][key_id].update(data)
        else:
            self.collection_data[key][key_id] = data

    def get_collection_data(self, key):
        if key in self.collection_data:
            return self.collection_data[key]
        else:
            return None

    def get_msg(self, key):
        if key in self.message_array:
            return self.message_array[key]
        else:
            return None

    def add_msg(self, key, data):
        self.message_array[key] = data

    def get_sub(self, key):
        if key in self.subscriptions_array:
            return self.subscriptions_array[key]
        else:
            return None

    def add_sub(self, key, data):
        self.subscriptions_array[key] = data
