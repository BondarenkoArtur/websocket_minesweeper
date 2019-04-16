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
                            if contains_result(data):
                                self.worker.on_login_response(data['result'])
                            else:
                                raise ValueError("Wrong login response")
                    elif is_system_configuration(self.data, data):
                        if contains_result(data):
                            self.worker.on_system_configuration_response(
                                data['result'])
                        else:
                            raise ValueError("Wrong system "
                                             "configuration response")
                    elif is_user_division(self.data, data):
                        if contains_result(data):
                            self.worker.on_user_division_response(
                                data['result'])
                        else:
                            raise ValueError("Wrong user "
                                             "division response")
                    elif is_system_deployment(self.data, data):
                        if contains_result(data):
                            self.worker.on_system_deployment_response(
                                data['result'])
                        else:
                            raise ValueError("Wrong system "
                                             "deployment response")
                    elif is_user_tooth_available(self.data, data):
                        if contains_result(data):
                            if available_in_result(data):
                                for i in range(data['result']['available']):
                                    self.worker.get_gold_tooth()
                            self.worker.on_user_tooth_available_response(
                                data['result'])
                        else:
                            raise ValueError("Wrong user tooth "
                                             "available response")
                    elif is_user_get_adv_bonus(self.data, data):
                        pass
                    elif is_enhancement_my(self.data, data):
                        if contains_result(data):
                            self.worker.on_enhancements_my_response(
                                data['result'])
                        else:
                            raise ValueError("Wrong enhancement my response")
                    else:
                        raise ValueError("Unknown result", data)
                else:
                    raise ValueError("Does not contains id", data)
            elif is_msg_added(data):
                if contains_collection(data) and contains_id(data):
                    self.worker.add_to_collection(data['collection'],
                                                  data['id'],
                                                  data['fields'])
                else:
                    raise ValueError("Unknown added msg")
            elif is_msg_changed(data):
                if contains_collection(data) and contains_id(data):
                    self.worker.add_to_collection(data['collection'],
                                                  data['id'],
                                                  data['fields'])
                else:
                    raise ValueError("Unknown changed msg")
            elif is_msg_ready(data):
                if contains_subs(data):
                    self.worker.ready_subs(data['subs'])
                else:
                    raise ValueError("Unknown ready msg")
            else:
                raise ValueError("Unknown msg type")
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


def is_msg_added(data):
    return data['msg'] == 'added'


def is_msg_changed(data):
    return data['msg'] == 'changed'


def is_msg_ready(data):
    return data['msg'] == 'ready'


def contains_id(data):
    return 'id' in data


def contains_result(data):
    return 'result' in data


def contains_collection(data):
    return 'collection' in data


def contains_subs(data):
    return 'subs' in data


def is_system_version(ext_data, data):
    return ext_data.get_msg(data['id'])['method'] == Commands.SYSTEM_VERSION


def is_login(ext_data, data):
    return ext_data.get_msg(data['id'])['method'] == Commands.LOGIN


def is_system_configuration(ext_data, data):
    return ext_data.get_msg(data['id'])['method'] == \
           Commands.SYSTEM_CONFIGURATION


def is_user_division(ext_data, data):
    return ext_data.get_msg(data['id'])['method'] == \
           Commands.USER_DIVISION


def is_system_deployment(ext_data, data):
    return ext_data.get_msg(data['id'])['method'] == \
           Commands.SYSTEM_DEPLOYMENT


def is_user_tooth_available(ext_data, data):
    return ext_data.get_msg(data['id'])['method'] == \
           Commands.USER_TOOTH_AVAILABLE


def is_user_get_adv_bonus(ext_data, data):
    return ext_data.get_msg(data['id'])['method'] == \
           Commands.USER_GET_ADV_BONUS


def is_enhancement_my(ext_data, data):
    return ext_data.get_msg(data['id'])['method'] == \
           Commands.ENHANCEMENT_MY


def available_in_result(data):
    return 'available' in data['result']


def is_contains_error(data):
    return 'error' in data


def is_error_incorrect_name(data):
    return data['error']['error'] == 'common.auth.incorrectName'
