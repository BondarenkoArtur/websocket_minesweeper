import json
from queue import Queue

from data.data import Data
from logic.commands import Commands
from logic.utils import generate_key


class Worker:
    def __init__(self, socket):
        self.request_queue = Queue()
        self.process_request = None

        self.msg_id = 0
        self.sub_id = 0
        self.data = Data()
        self.socket = socket

        self.google_id = None
        self.name = None
        self.is_first_time_login_with_name = True

    def get_data(self):
        return self.data

    def simulate_m_request(self, method, params=None):
        self.msg_id += 1
        string_id = "m%d" % self.msg_id
        if params is None:
            request = {"id": string_id,
                       "params": [],
                       "msg": "method",
                       "method": method}
        else:
            request = {"id": string_id,
                       "params": [params],
                       "msg": "method",
                       "method": method}
        self.data.add_msg(string_id, request)
        self.init_request(string_id)

    def simulate_sub_request(self, method, params=None):
        self.sub_id += 1
        string_id = "s%d" % self.sub_id
        if params is None:
            request = {"id": string_id,
                       "name": method,
                       "params": [],
                       "msg": "sub"}
        else:
            request = {"id": string_id,
                       "name": method,
                       "params": [params],
                       "msg": "sub"}
        self.data.add_sub(string_id, request)
        self.socket.send(json.dumps(request))

    def simulate_unsub_request(self, sub_string_id):
        request = {"id": sub_string_id,
                   "msg": "unsub"}
        self.socket.send(json.dumps(request))

    def login_with_google_play_id(self):
        if self.google_id is not None:
            self.simulate_m_request(Commands.LOGIN,
                                    {"name": "",
                                     "key": generate_key(self.google_id),
                                     "id": self.google_id,
                                     "gameService": True})
        else:
            raise ValueError("No google id set")

    def login_with_name(self):
        if self.is_first_time_login_with_name \
                and self.google_id is not None and self.name is not None:
            self.simulate_m_request(Commands.LOGIN,
                                    {"name": self.name,
                                     "key": generate_key(self.google_id),
                                     "id": self.google_id,
                                     "gameService": True})
            self.is_first_time_login_with_name = False
        else:
            raise ValueError("Wrong name for new account")

    def on_first_response(self):
        request = {"support": ["pre1"],
                   "msg": "connect",
                   "version": "pre1"}
        json_request = json.dumps(request)
        self.socket.send(json_request)

    def on_msg_connected(self, data):
        self.data.set_global_data('session', data['session'])
        self.simulate_m_request(Commands.SYSTEM_VERSION,
                                {"version": "2.17.1", "platform": "android"})

    def on_msg_updated(self, data):
        if 'methods' in data:
            for method in data['methods']:
                if self.process_request == method:
                    self.process_request = None
                    self.send_next_request()

    def init_request(self, string_id):
        self.request_queue.put(string_id)
        self.send_next_request()

    def send_next_request(self):
        if self.process_request is None:
            if not self.request_queue.empty():
                req = self.request_queue.get()
                request = self.data.get_msg(req)
                self.process_request = req
                self.socket.send(json.dumps(request))
            else:
                self.no_requests_left()

    def no_requests_left(self):
        raise NotImplementedError("Not implemented no_requests_left")
        pass

    def set_google_id(self, param):
        self.google_id = param

    def set_name(self, param):
        self.name = param

    def add_to_collection(self, key, key_id, data):
        self.data.set_collection_data(key, key_id, data)

    def on_login_response(self, response):
        self.data.set_global_data('id', response['id'])
        self.data.set_global_data('token', response['token'])
        self.data.set_global_data('tokenExpires', response['tokenExpires'])
        self.simulate_m_request(Commands.SYSTEM_CONFIGURATION)

    def on_system_configuration_response(self, response):
        self.data.set_global_data('time', response['time'])
        self.data.set_global_data('config', response['config'])
        self.start_subscriptions()
        self.simulate_m_request(Commands.USER_DIVISION, {"range": 0})

    def on_user_division_response(self, response):
        if type(response) == bool and response == False:
            self.simulate_m_request(Commands.SYSTEM_DEPLOYMENT)
        else:
            players = sorted(response['players'],
                             key=lambda kv: (kv['position']))
            self.data.set_global_data('players', players)
            self.data.set_global_data('divisionType', response['divisionType'])
            self.simulate_m_request(Commands.SYSTEM_DEPLOYMENT)

    def on_system_deployment_response(self, response):
        self.data.set_global_data('deployments', response['value'])
        self.simulate_m_request(Commands.USER_TOOTH_AVAILABLE)

    def on_enhancements_my_response(self, response):
        self.data.set_global_data('current', response['current'])
        self.data.set_global_data('next', response['next'])

    def on_user_tooth_available_response(self, response):
        self.simulate_m_request(Commands.ENHANCEMENT_MY)

    def get_gold_tooth(self):
        self.simulate_m_request(Commands.USER_GET_ADV_BONUS, {"type": "tooth"})

    def ready_subs(self, subs_list):
        for sub in subs_list:
            sub_elem = self.data.get_sub(sub)
            if sub_elem is not None:
                sub_elem['ready'] = True
        pass

    def start_subscriptions(self):
        self.simulate_sub_request(Commands.USER_CURRENT,
                                  params={"fields": ["lives",
                                                     "liveCooldown",
                                                     "workbench",
                                                     "rank"]})

        self.simulate_sub_request(Commands.USER_CURRENT,
                                  params={"fields": ["money",
                                                     "score"]})
        self.simulate_sub_request(Commands.COUNTS)
        self.simulate_sub_request(Commands.USER_ITEM_MY)
        self.simulate_sub_request(Commands.USER_ELEMENTS_MY)
        self.simulate_sub_request(Commands.NOTIFICATIONS_MY)
        self.simulate_sub_request(Commands.USER_EFFECTS_MY)
        self.simulate_sub_request(Commands.BATTLE_LIST)
