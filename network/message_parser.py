import json

from logic.commands import Commands


class Parser:
    def __init__(self, worker):
        self.worker = worker
        self.data = worker.get_data()

    def parse_message(self, message):
        data = json.loads(message)
        self.parse_data(data)

    def parse_data(self, data):
        if is_first_response(data):
            self.worker.on_first_response()
        elif is_main_response_message(data):
            if is_msg_updated(data):
                self.worker.on_msg_updated(data)
            elif is_msg_connected(data):
                self.worker.on_msg_connected(data)
            elif is_msg_result(data):
                if contains_id(data):
                    if is_system_version(self.data, data):
                        self.worker.login_with_google_play_id()
                    elif is_login(self.data, data):
                        if is_contains_error(data):
                            if is_error_incorrect_name(data):
                                self.worker.login_with_name()
                            else:
                                raise ValueError("Unknown login error", data)
                        else:
                            raise NotImplementedError("Not implemented "
                                                      "action on login")
                    else:
                        raise ValueError("Unknown result", data)
                else:
                    raise ValueError("Does not contains id", data)
        else:
            raise NotImplementedError("Not implemented "
                                      "parsing of this data", data)


def is_first_response(data):
    return 'server_id' in data and data['server_id'] == '0'


def is_main_response_message(data):
    return 'msg' in data


def is_msg_connected(data):
    return data['msg'] == 'connected'


def is_msg_updated(data):
    return data['msg'] == 'updated'


def is_msg_result(data):
    return data['msg'] == 'result'


def contains_id(data):
    return 'id' in data


def is_system_version(ext_data, data):
    return ext_data.get_msg(data['id'])['method'] == Commands.SYSTEM_VERSION


def is_login(ext_data, data):
    return ext_data.get_msg(data['id'])['method'] == Commands.LOGIN


def is_contains_error(data):
    return 'error' in data


def is_error_incorrect_name(data):
    return data['error']['error'] == 'common.auth.incorrectName'
