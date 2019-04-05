import json
import threading
from datetime import datetime
from pprint import pprint
from queue import Queue

import websocket

try:
    import thread
except ImportError:
    import _thread as thread
import time

request_queue = Queue()

debug = False

msg_id = 0
sub_id = 0
sweeperSocket = None
process_request = None

msg_array = {}
sub_array = {}
enabled_subs = []

from local_data import login_data_array, counts_data_array, items_data_array, \
    battles_data_array, battles_full_data_array, current_map_info, sweeper_map, \
    current_map_item_info, bot_on, previous_item_info, enhancements_array, \
    current_map_all_item_info


def new_parse_message(message):
    data = json.loads(message)
    if 'msg' in data and data['msg'] == 'c':
        # we're not printing huge arrays of coordinates
        pass
    else:
        if debug:
            pprint(data)
    if 'server_id' in data:
        if data['server_id'] == '0':
            simulate_pre_request()
        else:
            unknown_error(101, message)
    elif 'msg' in data:
        if data['msg'] == 'updated':
            if 'methods' in data:
                global process_request
                for meth in data['methods']:
                    if process_request == meth:
                        process_request = None
                        send_next_request()
            else:
                unknown_error(102, message)
        elif data['msg'] == 'connected':
            # login with platform
            login_data_array['session'] = data['session']
            simulate_m_request("system.version",
                               {"version": "2.17.1", "platform": "android"})
        elif data['msg'] == 'result':
            if 'id' in data:
                if data['id'] in msg_array:
                    if msg_array[data['id']]['method'] == 'system.version':
                        # login with google play id
                        g_id = "g08745036216621216599"
                        # g_id = "g15649493212719029158"
                        simulate_m_request("login", {"name": "",
                                                     "key": generate_key(g_id),
                                                     "id": g_id,
                                                     "gameService": True})
                    elif msg_array[data['id']]['method'] == 'login':
                        if 'result' in data:
                            login_data_array['login_result'] = data['result']
                            simulate_m_request("system.configuration")
                        else:
                            unknown_error(141, message)
                    elif msg_array[data['id']]['method'] == \
                            'system.configuration':
                        simulate_sub_request("users.current", params={
                            "fields": ["lives", "liveCooldown",
                                       "workbench", "rank"]})
                        # "fields": ["lives", "liveCooldown", "money", "score",
                        # "workbench", "rank"]})
                        # simulate_sub_request("users.current", params={
                        #     "fields": ["money", "score"]})
                        simulate_sub_request("counts")
                        simulate_sub_request("user_item.my")
                        simulate_sub_request("user_elements.my")
                        simulate_sub_request("notifications.my")
                        simulate_sub_request("user_effects.my")
                        simulate_sub_request("battle.list")
                        simulate_m_request("user.division", {"range": 1})
                    elif msg_array[data['id']]['method'] == 'user.division':
                        if 'result' in data:
                            if 'players' in data['result']:
                                counts_data_array['division'] = \
                                    data['result']['players']
                                if 'divisionType' in data['result']:
                                    counts_data_array['divisionType'] = \
                                        data['result']['divisionType']
                                else:
                                    unknown_error(122, message)
                                simulate_m_request("system.deployment")
                            else:
                                unknown_error(121, message)
                        else:
                            unknown_error(120, message)
                    elif msg_array[data['id']]['method'] == \
                            'system.deployment':
                        # todo Save IPs from request
                        simulate_m_request("user.tooth_available")
                        simulate_m_request("enhancement.my")
                    elif msg_array[data['id']]['method'] == \
                            'user.tooth_available':
                        if 'result' in data:
                            parse_user_tooth(data)

                            # todo add logic for selection world
                            # instead of Preset4_1
                            # 1 - red
                            # 2 - yellow
                            # 3 - green
                            # 4 - blue
                            # 5 - magenta
                            simulate_m_request("battle.enter", {
                                "battleId": battles_data_array['Preset4_1']})
                        else:
                            unknown_error(123, message)
                    elif msg_array[data['id']]['method'] == \
                            'user.get_adv_bonus':
                        # todo check what messages are coming here and if
                        # needed create parser
                        pass
                    elif msg_array[data['id']]['method'] == "battle.enter":
                        if 'result' in data:
                            parse_battle_enter(data)
                        else:
                            unknown_error(126, message)
                    elif msg_array[data['id']]['method'] == "battle.move":
                        # probably do nothing
                        pass
                    elif msg_array[data['id']]['method'] == "battle.teleport":
                        if 'result' in data:
                            current_map_info['coords'] = data['result']
                            battle_move_to()
                            # simulate_m_request("battle.move",
                            #                    current_map_info['coords'])
                        else:
                            unknown_error(133, message)
                    elif msg_array[data['id']]['method'] == "enhancement.my":
                        if 'result' in data:
                            parse_enhancements(data)
                        else:
                            unknown_error(140, message)
                    elif msg_array[data['id']]['method'] == "field.flag":
                        if 'result' in data:
                            if type(data['result']) == bool:
                                if data['result']:
                                    # do nothing, it's success
                                    pass
                                else:
                                    # todo check is false possible
                                    unknown_error(136, message)
                            else:
                                unknown_error(135, message)
                        else:
                            unknown_error(134, message)
                    elif msg_array[data['id']]['method'] == "field.open":
                        # do nothing, it's success
                        # might be that here will be false in some case, but
                        # I'm not sure
                        pass
                    elif msg_array[data['id']]['method'] == "field.sell":
                        # do nothing, it's success
                        # might be that here will be false in some case, but
                        # I'm not sure
                        pass
                    elif msg_array[data['id']]['method'] == "field.pick":
                        # do nothing, it's success
                        # might be that here will be false in some case, but
                        # I'm not sure
                        pass
                    elif msg_array[data['id']]['method'] == "enhancement.buy":
                        # do nothing, it's success
                        # might be that here will be false in some case, but
                        # I'm not sure
                        pass
                    elif msg_array[data['id']]['method'] == "notification.use":
                        # do nothing, it's success
                        # might be that here will be false in some case, but
                        # I'm not sure
                        pass
                    elif msg_array[data['id']]['method'] == "user_item.sell":
                        # do nothing, it's success
                        # might be that here will be false in some case, but
                        # I'm not sure
                        pass
                    else:
                        unknown_error(103, message)
                else:
                    unknown_error(104, message)
            else:
                unknown_error(105, message)
        elif data['msg'] == 'added':
            if 'collection' in data:
                if data['collection'] == 'users':
                    if 'fields' in data:
                        parse_users(data)
                    else:
                        unknown_error(106, message)
                elif data['collection'] == 'user_items':
                    if 'fields' in data:
                        parse_user_items(data)
                    else:
                        unknown_error(116, message)
                elif data['collection'] == 'user_elements':
                    if 'fields' in data:
                        parse_user_elements(data)
                    else:
                        unknown_error(117, message)
                elif data['collection'] == 'battles':
                    if 'fields' in data:
                        parse_battles(data)
                    else:
                        unknown_error(119, message)
                elif data['collection'] == 'counts':
                    if 'fields' in data:
                        parse_counts(data)
                    else:
                        unknown_error(137, message)
                elif data['collection'] == 'notifications':
                    if 'fields' in data:
                        parse_notifications(data)
                    else:
                        unknown_error(142, message)
                else:
                    unknown_error(107, message)
            else:
                unknown_error(108, message)
        elif data['msg'] == 'changed':
            if 'collection' in data:
                if data['collection'] == 'users':
                    if 'fields' in data:
                        if 'fields' in login_data_array:
                            login_data_array['fields'].update(
                                data['fields'])
                        else:
                            login_data_array['fields'] = data['fields']
                    else:
                        unknown_error(112, message)
                elif data['collection'] == 'user_elements':
                    if 'fields' in data:
                        parse_user_elements(data)
                    else:
                        unknown_error(132, message)
                elif data['collection'] == 'user_items':
                    if 'fields' in data:
                        parse_user_items(data)
                    elif 'cleared' in data:
                        # probably do nothing
                        pass
                    else:
                        unknown_error(145, message)
                elif data['collection'] == 'battles':
                    if 'fields' in data:
                        parse_battles(data)
                    elif 'cleared' in data:
                        # todo do something with this data
                        pass
                    else:
                        unknown_error(125, message)
                elif data['collection'] == 'counts':
                    if 'fields' in data:
                        parse_counts(data)
                    else:
                        unknown_error(139, message)
                else:
                    unknown_error(111, message)
            else:
                unknown_error(110, message)
        elif data['msg'] == 'ready':
            if 'subs' in data:
                for sub in data['subs']:
                    if sub in sub_array:
                        enabled_subs.append(sub)
                    else:
                        unknown_error(115, message)
            else:
                unknown_error(114, message)
        elif data['msg'] == 'removed':
            if 'collection' in data:
                if data['collection'] == 'battles':
                    # todo maybe add deleting items from collection
                    pass
                elif data['collection'] == 'notifications':
                    pass
                else:
                    unknown_error(128, message)
            else:
                unknown_error(127, message)
        elif data['msg'] == 'nosub':
            if 'id' in data:
                if data['id'] in sub_array:
                    del sub_array[data['id']]
                    enabled_subs.remove(data['id'])
                else:
                    unknown_error(130, message)
            else:
                unknown_error(129, message)
        elif data['msg'] == 'c':
            if 'ds' in data:
                for elem in data['ds']:
                    append_element(elem)
            elif 'd' in data:
                append_element(data['d'])
            else:
                unknown_error(131, message)
        else:
            unknown_error(109, message)



    # elif 'collection' in data and data['collection'] == 'notifications':
    #     # todo parse other notifications
    #     if 'fields' in data and 'type' in data['fields'] and (data['fields']['type'] == 'division' or data['fields']['type'] == 'reward'):
    #         if 'value' in data['fields'] and 'id' in data:
    #             # {"msg":"added","collection":"notifications","id":"2059f5c9-b6f8-5ebb-bb86-266b21b7f686","fields":{"type":"division","value":{"previous":{"absoluteNumber":1,"league":"bronze","number":1,"position":1},"current":{"absoluteNumber":2,"league":"bronze","number":2},"reward":{"money":5000}}}}
    #             # {"id":"m13","msg":"method","method":"notification.use","params":[{"notificationId":"2059f5c9-b6f8-5ebb-bb86-266b21b7f686"}]}
    #             simulate_m_request("notification.use", params={"notificationId":data['id']})
    #             pass


def parse_notifications(data):
    # todo showing notifications on UI
    if 'type' in data['fields']:
        if data['fields']['type'] == 'division':
            simulate_m_request("notification.use",
                               params={"notificationId": data['id']})
        elif data['fields']['type'] == 'reward':
            simulate_m_request("notification.use",
                               params={"notificationId": data['id']})
        elif data['fields']['type'] == 'enhancement':
            simulate_m_request("notification.use",
                               params={"notificationId": data['id']})
        elif data['fields']['type'] == 'rank':
            simulate_m_request("notification.use",
                               params={"notificationId": data['id']})
        else:
            unknown_error(144, json.dumps(data))
    else:
        unknown_error(143, json.dumps(data))

def parse_enhancements(data):
    if 'current' in data['result']:
        enhancements_array['current'] = data['result']['current']
        for cur in enhancements_array['current']:
            if 'upgrade' in cur:
                if 'advAvailable' in cur['upgrade'] and \
                                cur['upgrade']['advAvailable'] > 0:
                    for i in range(cur['upgrade']['advAvailable']):
                        simulate_m_request("user.get_adv_bonus",
                                           {"type": "skill_upgrade_time"})
    if 'next' in data ['result']:
        enhancements_array['next'] = data['result']['next']
    pass


def parse_counts(data):
    if 'count' in data['fields']:
        counts_data_array['count'] = data['fields']['count']
    else:
        unknown_error(138, json.dumps(data))


def parse_battle_enter(data):
    current_map_info['coords'] = data['result']
    # todo add logic for selection world instead of Preset4_1
    simulate_sub_request("battle.single", params={
        "battleId": battles_data_array['Preset4_1']})
    battle_move_to()
    # simulate_m_request("battle.move", current_map_info['coords'])
    for elem in sub_array.values():
        if elem['name'] == 'battle.list':
            simulate_unsub_request(elem['id'])


def parse_user_tooth(data):
    if 'available' in data['result']:
        if data['result']['available'] > 0:
            for i in range(data['result']['available']):
                simulate_m_request("user.get_adv_bonus",{"type": "tooth"})
    else:
        unknown_error(124, json.dumps(data))


def parse_battles(data):
    battles_full_data_array[data['id']] = data['fields']
    battles_data_array[data['fields']['presetId']] = data['id']


def parse_user_items(data):
    # todo check is this possible to improve somehow
    if not 'locked' in data['fields'] or (
            'locked' in data['fields'] and not data['fields']['locked']):
        if 'item' in data['fields']:
            d = [data['id'], data['fields']['item']['key'],
                 data['fields']['item']['rating']]
            if 'upgrade' in data['fields']:
                if 'advAvailable' in data['fields']['upgrade'] and \
                                data['fields']['upgrade']['advAvailable'] > 0:
                    for i in range(data['fields']['upgrade']['advAvailable']):
                        simulate_m_request("user.get_adv_bonus",
                                           {"type": "gem_upgrade_time"})
                ts = data['fields']['upgrade']['finishAt']
                ts /= 1000
                d1 = datetime.utcfromtimestamp(ts)
                d.append(str(d1))
        elif 'upgrade' in data['fields']:
            slots = [key for key, value in
                     items_data_array.items() if
                     data['id'] in value]
            ts = data['fields']['upgrade']['finishAt']
            ts /= 1000
            d1 = datetime.utcfromtimestamp(ts)
            items_data_array[slots[0]][3] = str(d1)
            d = items_data_array[slots[0]]
        else:
            d = [data['id'], None, 0]
        if 'type' in data['fields']:
            items_data_array[data['fields']['type'] + \
                             str(data['fields'][
                                     'slot'])] = d
        else:
            slots = [key for key, value in
                     items_data_array.items() if
                     data['id'] in value]
            items_data_array[slots[0]] = d


def parse_user_elements(data):
    if 'amount' in data['fields']:
        items_data_array[data['id']] = data['fields']
    else:
        unknown_error(118, json.dumps(data))


def parse_users(data):
    if 'profile' in data['fields']:
        login_data_array['profile'] = \
            data['fields']['profile']
        login_data_array['profile_id'] = data['id']
    else:
        unknown_error(113, json.dumps(data))

def unknown_error(err_id, message):
    print(">>> UNKNOWN PACKET %d <<< %s" % (err_id, message))

def append_element(elem):
    if len(elem) == 2:
        elem.append(-1)
    if check_is_item(elem):
        item_id = process_item(elem)
        sweeper_map[elem[0]][elem[1]] = item_id
    else:
        sweeper_map[elem[0]][elem[1]] = elem[2]

def process_item(elem):
    current_map_all_item_info["%d,%d" % (elem[0], elem[1])] = elem[2]
    if elem[2]['userId'] == login_data_array['profile_id']:
    # if True:
        mine = (elem[0], elem[1], elem[2])
        if 'key' in elem[2] and 'chest' in elem[2]['key']:
            if 'items' in elem[2]:
            # if True:
                if mine not in current_map_item_info:
                    current_map_item_info.append(mine)
                    # todo add check is auto pick up
                    pick_on_map(elem[0], elem[1])
                    return -9
        elif mine not in current_map_item_info:
            current_map_item_info.append(mine)
            # todo add check is auto pick up
            pick_on_map(elem[0], elem[1])
            return -9
    return -8

def check_is_item(elem):
    if type(elem[2]) is dict:
        return True
    else:
        return False

def simulate_pre_request():
    request = {"support": ["pre1"],
               "msg": "connect",
               "version": "pre1"}
    json_request = json.dumps(request)
    if debug:
        print(">>> pre req: %s" % json_request)
    sweeperSocket.send(json_request)

# todo requests

# {"params":[{"battleId":"a4e9d57f-57c7-5a40-a9bf-d82f0afa9591"}],"id":"m24","method":"battle.items","msg":"method"}
# {"params":[],"id":"m25","method":"user.money","msg":"method"}
# {"params":[{"battleId":"a4e9d57f-57c7-5a40-a9bf-d82f0afa9591"}],"id":"m26","method":"battle_user.top","msg":"method"}
# {"params":[{}],"id":"m27","method":"battle.exit","msg":"method"}
# {"name":"users.current","params":[{"fields":["money","score"]}],"id":"s10","msg":"sub"} # maybe...
# {"params":[],"id":"m28","method":"battle_user.progress","msg":"method"}


# {"id":"m7","params":[{"type":"magenta_gem","slot":0}],"msg":"method","method":"user_item.finishUpgrade"}
# {"id":"m8","params":[{"type":"green_gem","slot":3}],"msg":"method","method":"user_item.recipes"}
# {"id":"m9","params":[{"type":"green_gem","recipeId":"GreenGemLevel5","slot":3,"workbench":1}],"msg":"method","method":"user_item.upgrade"}
# {"id":"m14","params":[{"userId":"CoYHBYfSQfAj3b9so"}],"msg":"method","method":"user.profile"}

# {"msg":"method","id":"m7","params":[{"type":"red_gem","from":2,"to":0}],"method":"user_item.move"}
# {"id":"m16","params":[{"type":"blue_gem","slot":0}],"method":"user_item.sell","msg":"method"}
# {"id":"m18","params":[{"type":"blue_gem","to":0,"from":1}],"method":"user_item.move","msg":"method"}

# {"msg":"method","id":"m15","params":[{"type":"skill_upgrade_time"}],"method":"user.get_adv_bonus"}
# {"msg":"added","collection":"notifications","id":"55d06c23-df33-5ac9-9dda-cffc8288b264","fields":{"type":"enhancement","value":{"type":"upgrade_cost","level":2}}}
# {"msg":"method","id":"m17","params":[{"notificationId":"55d06c23-df33-5ac9-9dda-cffc8288b264"}],"method":"notification.use"}
# {"msg":"method","id":"m12","params":[{"type":"upgrade_cost"}],"method":"enhancement.buy"}

def simulate_m_request(method, params=None):
    global msg_id
    msg_id += 1
    string_id = "m%d" % msg_id
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
    msg_array[string_id] = request
    init_request(string_id)
    # ws.send(json_request)


def init_request(string_id):
    request_queue.put(string_id)
    send_next_request()



def send_next_request():
    global process_request, request_queue
    if process_request is None:
        if not request_queue.empty():
            req = request_queue.get()
            request = msg_array[req]
            if debug:
                print(">>> %s: %s" % (req, request))
            process_request = req
            # time.sleep(1)
            sweeperSocket.send(json.dumps(request))
        else:
            check_is_needed_solving()



def simulate_sub_request(name, params=None):
    global sub_id
    sub_id += 1
    string_id = "s%d" % sub_id
    if params is None:
        request = {"name": name,
                   "id": string_id,
                   "params": [],
                   "msg": "sub"}
    else:
        request = {"name": name,
                   "id": string_id,
                   "params": [params],
                   "msg": "sub"}
    sub_array[string_id] = request
    json_request = json.dumps(request)
    if debug:
        print(">>> %s: %s" % (string_id, json_request))
    sweeperSocket.send(json_request)


def simulate_unsub_request(sub_string_id):
    request = {"id": sub_string_id,
               "msg": "unsub"}
    json_request = json.dumps(request)
    if debug:
        print(">>> unsub %s: %s" % (sub_string_id, json_request))
    sweeperSocket.send(json_request)


def on_message(ws, message):
    new_parse_message(message)
    # parse_message(message)


def on_error(ws, error):
    print(error)
    pass


def on_close(ws):
    # todo probably reopen remote connection on close
    print("### closed ###")
    print_all_data()
    pass


def on_open(ws):
    def run(*args):
        for i in range(3):
            time.sleep(1)
            ws.send("Hello %d" % i)
        time.sleep(1)
        ws.close()
        #print("thread terminating...")

    thread.start_new_thread(run, ())


def generate_key(g_id):
    import hashlib
    return hashlib.md5((g_id+"griff").encode('utf-8')).hexdigest()

def battle_move_to():
    if sweeperSocket is not None:
        new_coords = current_map_info['coords']
        new_coords['x'] = (new_coords['x'] // 20) * 20 + 10
        new_coords['y'] = (new_coords['y'] // 20) * 20 + 10
        simulate_m_request("battle.move", new_coords)


def move_on_map(x, y):
    if sweeperSocket is not None and 'coords' in current_map_info:
        new_coords = current_map_info['coords']
        new_coords['x'] += x
        new_coords['y'] += y
        battle_move_to()


def get_available_gem_space(map_item):
    key_find = map_item['key']
    pickup_rating = 0
    if enhancements_array is not None:
        if 'current' in enhancements_array:
            for enh in enhancements_array['current']:
                if enh['type'] == 'pickup_rating':
                    pickup_rating = enh['value']
    slots = [key for key, value in items_data_array.items() if
           key_find[0:3] in key]
    if len(slots) > 0:
        min_value = items_data_array[slots[0]][2]
        min_element = slots[0]
        for slot in slots:
            item = items_data_array[slot]
            if min_value > item[2]:
                min_value = item[2]
                min_element = slot
        if min_value > map_item['rating'] + pickup_rating:
            return -1
        elif items_data_array[min_element][1] is not None:
            sell_gem(min_element)
        return int(min_element[-1])



def sell_gem(element):
    gem_type = element[0:-1]
    slot = int(element[-1])
    simulate_m_request("user_item.sell", params={"type":gem_type, "slot":slot})



def pick_on_map(x, y):
    # todo check if key picked up do we refresh field
    if sweeperSocket is not None and 'coords' in current_map_info:
        to_delete_item = None
        for item in current_map_item_info:
            if item[0] == x and item[1] == y:
                if item[2]['userId'] == login_data_array['profile_id']:
                    if 'gem' in item[2]['key']:
                        slot = get_available_gem_space(item[2])
                        if slot == -1:
                            # in case if gem cheap - sell it
                            simulate_m_request("field.sell", params={"y":y, "x":x})
                        else:
                            simulate_m_request("field.pick", params={"y":y, "x":x, "slot":slot})
                        to_delete_item = item
                    else:
                        simulate_m_request("field.pick", params={"y":y, "x":x})
                        to_delete_item = item
        if to_delete_item is not None:
            current_map_item_info.remove(to_delete_item)
            previous_item_info.insert(0, to_delete_item)
            if len(previous_item_info) > 5:
                previous_item_info.pop()

def flag_on_map(x, y):
    if sweeperSocket is not None and 'coords' in current_map_info:
        simulate_m_request("field.flag", params={"y":y, "x":x})

def open_on_map(x, y):
    if sweeperSocket is not None and 'coords' in current_map_info:
        simulate_m_request("field.open", params={"y":y, "x":x})

def teleport():
    if sweeperSocket is not None and 'coords' in current_map_info:
        simulate_m_request("battle.teleport")

def switch_debug():
    global debug
    debug = not debug

# Actually if this is bigger than 38, sometimes it tries to open or set a flag
# but because of being far from coordinates in middle, it just doesn't refresh.
# So there is few variants:
# 1. Drop cache after teleport
# 2. Move coordinates to where it should change
#
# Now it is 58, because size of loaded field is 60x60, so if it's loaded
# properly, we can easily solve in 58x58 area. Cells outside of 60x60 area are
# not loaded, so any flag or opens will not be visible.
sweeper_width = 58
sweeper_height = 58


def is_dangerous(x, y):
    cell = sweeper_map[x][y]
    return cell == 10 or cell == 11 or cell == -10


def is_proxy(x, y):
    cell = sweeper_map[x][y]
    return 1 <= cell < 9


def get_neighbors(x, y):
    neigh = []
    for i in range(3):
        for j in range(3):
            local_x = x + i - 1
            local_y = y + j - 1
            if 0 <= local_x < 2000 and 0 <= local_y < 2000:
                neigh.append([local_x, local_y])
    return neigh


def get_hidden_neighbors(x, y):
    neigh = get_neighbors(x, y)
    hid_neigh = []
    for neig in neigh:
        if sweeper_map[neig[0]][neig[1]] == -1:
            hid_neigh.append(neig)
    return hid_neigh


def is_outdated(x, y):
    cell = sweeper_map[x][y]
    dangerous = get_dangerous(x, y)
    return cell == len(dangerous)


def get_dangerous(x, y):
    neigh = get_neighbors(x, y)
    dangerous = []
    for neig in neigh:
        if is_dangerous(neig[0], neig[1]):
            dangerous.append(neig)
    return dangerous


def is_any_empty_neighbors(x, y):
    neigh = get_neighbors(x, y)
    for neig in neigh:
        if sweeper_map[neig[0]][neig[1]] == -10:
            return True
    return False


def do_check(x, y):
    if is_proxy(x, y) and not is_any_empty_neighbors(x, y):
        gold = get_hidden_neighbors(x, y)
        if is_outdated(x, y):
            if len(gold) > 0:
                open_on_map(x, y)
                return True
        else:
            dangerous = get_dangerous(x, y)
            if len(gold) + len(dangerous) == sweeper_map[x][y]:
                flag_on_map(x, y)
                return True
    return False


def try_to_solve():
    if sweeperSocket is not None and 'coords' in current_map_info:
        global sweeper_width, sweeper_height
        amount_solved = 0
        for k in range(sweeper_width + sweeper_height):
            for j in range(k):
                i = k - j - 1
                if i < sweeper_height and j < sweeper_width:
                    check_x = current_map_info['coords'][
                        'x'] - sweeper_width // 2 + i
                    check_y = current_map_info['coords'][
                        'y'] - sweeper_height // 2 + j
                    if 0 <= check_x < 2000 and 0 <= check_y < 2000:
                        if do_check(check_x, check_y):
                            amount_solved += 1
        if amount_solved == 0:
            teleport()
            disable_solving()
            threading.Timer(3, enable_solving).start()


solving = False
pause_solving = False

def check_is_needed_solving():
    global solving, pause_solving
    if solving:
        bot_on[0] = 1
    else:
        bot_on[0] = 0
    if solving and not pause_solving:
        solver = threading.Thread(target=try_to_solve)
        solver.daemon = True
        solver.start()


def enable_solving():
    global pause_solving
    pause_solving = False
    check_is_needed_solving()

def disable_solving():
    global pause_solving
    pause_solving = True
    check_is_needed_solving()

def switch_solving():
    global solving
    solving = not solving
    check_is_needed_solving()

def print_all_data():
    pprint(counts_data_array)
    pprint(current_map_info)
    pprint(current_map_item_info)
    pprint(login_data_array)
    pprint(items_data_array)
    pprint(battles_data_array)


def run_ws():
    global sweeperSocket
    # websocket.enableTrace(True)
    sweeperSocket = websocket.WebSocketApp(
        "ws://minesweeper.griffgriffgames.com/websocket",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close)
    # ws.on_open = on_open
    wst = threading.Thread(target=sweeperSocket.run_forever)
    wst.daemon = True
    wst.start()

if __name__ == "__main__":
    run_ws()
    input()


