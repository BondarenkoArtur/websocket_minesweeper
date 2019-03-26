import json
import threading
from pprint import pprint
from queue import Queue

import websocket

try:
    import thread
except ImportError:
    import _thread as thread
import time

request_queue = Queue()

msg_id = 0
sub_id = 0
sweeperSocket = None
process_request = None

# TODO put all elements through msg_array
msg_array = {}
sub_array = {}

from local_data import login_data_array, counts_data_array, items_data_array, \
    battles_data_array, battles_full_data_array, current_map_info, sweeper_map, \
    current_map_item_info, bot_on, previous_item_info


def parse_message(message, ws):
    data = json.loads(message)
    if 'msg' in data and data['msg'] == 'c':
        pass
    else:
        pprint(data)
    if 'msg' in data and data['msg'] == 'updated':
        if 'methods' in data:
            global process_request
            for meth in data['methods']:
                if process_request == meth:
                    process_request = None
                    send_next_request()
    elif 'server_id' in data and data['server_id'] == '0':
        simulate_pre_request(ws)
    elif 'msg' in data and data['msg'] == 'connected':
        # login with platform
        login_data_array['session'] = data['session']
        simulate_m_request(ws, "system.version", {"version": "2.17.1", "platform": "android"})
    elif 'id' in data and data['id'] in msg_array and msg_array[data['id']]['method'] == 'system.version':
        # login with google play id
        g_id = "g08745036216621216599"
        # g_id = "g15649493212719029158"
        simulate_m_request(ws, "login", {"name": "", "key": generate_key(g_id),
                    "id": g_id, "gameService": True})
    elif 'collection' in data and data['collection'] == 'users':
        # parse current user
        if 'fields' in data and 'profile' in data['fields']:
            login_data_array['profile'] = data['fields']['profile']
            login_data_array['profile_id'] = data['id']
        if 'fields' in data:
            if 'fields' in login_data_array:
                login_data_array['fields'].update(data['fields'])
            else:
                login_data_array['fields'] = data['fields']
    elif 'id' in data and data['id'] in msg_array and msg_array[data['id']]['method'] == 'login':
        login_data_array['login_result'] = data['result']
        simulate_m_request(ws, "system.configuration")
    elif 'id' in data and data['id'] in msg_array and msg_array[data['id']]['method'] == 'system.configuration':
        simulate_sub_request(ws, "users.current", params={
            "fields": ["lives", "liveCooldown", "workbench", "rank"]})
            # "fields": ["lives", "liveCooldown", "money", "score", "workbench", "rank"]})
        simulate_sub_request(ws, "counts")
        simulate_sub_request(ws, "user_item.my")
        simulate_sub_request(ws, "user_elements.my")
        simulate_sub_request(ws, "notifications.my")
        simulate_sub_request(ws, "user_effects.my")
        simulate_sub_request(ws, "battle.list")
        simulate_m_request(ws, "user.division", {"range": 1})
    elif 'collection' in data and data['collection'] == 'counts':
        if 'fields' in data and 'count' in data['fields']:
            counts_data_array['count'] = data['fields']['count']
    elif 'collection' in data and data['collection'] == 'user_items':
        if 'fields' in data :
            if not 'locked' in data['fields'] or ('locked' in data['fields'] and not data['fields']['locked']):
                if 'item' in data['fields']:
                    d = [data['id'], data['fields']['item']['key'],
                         data['fields']['item']['rating']]
                else:
                    d = [data['id'], None, 0]
                if 'type' in data['fields']:
                    items_data_array[data['fields']['type'] + \
                                 str(data['fields']['slot'])] = d
                else:
                    slots = [key for key, value in items_data_array.items() if
                             data['id'] in value]
                    items_data_array[slots[0]] = d
    elif 'collection' in data and data['collection'] == 'user_elements':
        if 'fields' in data and 'amount' in data['fields']:
            items_data_array[data['id']] = data['fields']
    elif 'collection' in data and data['collection'] == 'battles':
        if 'fields' in data:
            battles_full_data_array[data['id']] = data['fields']
            battles_data_array[data['fields']['presetId']] = data['id']
    elif 'id' in data and data['id'] in msg_array and msg_array[data['id']]['method'] == 'user.division':
        if 'result' in data and 'players' in data['result']:
            counts_data_array['division'] = data['result']['players']
            simulate_m_request(ws, "system.deployment")
    elif 'id' in data and data['id'] in msg_array and msg_array[data['id']]['method'] == 'system.deployment':
        # todo Save IPs from request
        simulate_m_request(ws, "user.tooth_available")
    elif 'id' in data and data['id'] in msg_array and msg_array[data['id']]['method'] == 'user.tooth_available':
        if 'result' in data and 'available' in data['result']:
            if data['result']['available'] > 0:
                simulate_m_request(ws, "user.get_adv_bonus", {"type":"tooth"})
            # todo add logic for selection world instead of Preset4_1
            # 1 - red
            # 2 - yellow
            # 3 - green
            # 4 - blue
            # 5 - magenta
            simulate_m_request(ws, "battle.enter", {"battleId": battles_data_array['Preset4_1']})
    elif 'id' in data and data['id'] in msg_array and msg_array[data['id']]['method'] == 'user.get_adv_bonus':
        pass
    elif 'id' in data and data['id'] in msg_array and msg_array[data['id']]['method'] == 'battle.enter':
        if 'msg' in data and data['msg'] == 'result':
            if 'result' in data:
                current_map_info['coords'] = data['result']
                # todo add logic for selection world instead of Preset4_1
                simulate_sub_request(ws, "battle.single", params={
                    "battleId": battles_data_array['Preset4_1']})
                simulate_m_request(ws, "battle.move",
                                   current_map_info['coords'])
                sub_str_id = None
                for elem in sub_array.values():
                    if elem['name'] == 'battle.list':
                        sub_str_id = elem['id']
                        simulate_unsub_request(ws, elem['id'])
                if sub_str_id is not None:
                    del sub_array[sub_str_id]
    elif 'id' in data and data['id'] in msg_array and msg_array[data['id']]['method'] == 'battle.teleport':
        if 'msg' in data and data['msg'] == 'result':
            if 'result' in data:
                current_map_info['coords'] = data['result']
                simulate_m_request(ws, "battle.move",
                                   current_map_info['coords'])
    elif 'id' in data and data['id'] in msg_array and msg_array[data['id']]['method'] == 'battle.move':
        if 'msg' in data and data['msg'] == 'result':
            # probably do nothing
            pass
    elif 'collection' in data and data['collection'] == 'notifications':
        # todo parse other notifications
        if 'fields' in data and 'type' in data['fields'] and data['fields']['type'] == 'division':
            if 'value' in data['fields'] and 'id' in data:
                # {"msg":"added","collection":"notifications","id":"2059f5c9-b6f8-5ebb-bb86-266b21b7f686","fields":{"type":"division","value":{"previous":{"absoluteNumber":1,"league":"bronze","number":1,"position":1},"current":{"absoluteNumber":2,"league":"bronze","number":2},"reward":{"money":5000}}}}
                # {"id":"m13","msg":"method","method":"notification.use","params":[{"notificationId":"2059f5c9-b6f8-5ebb-bb86-266b21b7f686"}]}
                simulate_m_request(ws, "notification.use", params={"notificationId":data['id']})
                pass

    elif 'msg' in data and (data['msg'] == 'ready' or data['msg'] == 'nosub' or  data['msg'] == 'result'):
        # pprint(data)
        # probably do nothing
        pass
    elif 'msg' in data and data['msg'] == 'c':
        # todo check is here overwriting or just adding on top
        if 'ds' in data:
            for elem in data['ds']:
                append_element(elem)
        if 'd' in data:
            elem = data['d']
            append_element(elem)
    else:
        print(">>> UNKNOWN PACKET <<<")


def append_element(elem):
    if len(elem) == 2:
        elem.append(-1)
    if check_is_item(elem):
        item_id = process_item(elem)
        sweeper_map[elem[0]][elem[1]] = item_id
    else:
        sweeper_map[elem[0]][elem[1]] = elem[2]

def process_item(elem):
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
    return 0

def check_is_item(elem):
    if type(elem[2]) is dict:
        return True
    else:
        return False

def simulate_pre_request(ws):
    request = {"support": ["pre1"],
               "msg": "connect",
               "version": "pre1"}
    json_request = json.dumps(request)
    print(">>> m req: %s" % json_request)
    ws.send(json_request)

# todo requests
# simulate_m_request(ws, "field.pick", {"y":1229,"slot":0,"x":1222})
# {"id":"m11","msg":"method","method":"field.pick","params":[{"y":1117,"slot":1,"x":425}]}
# {"id":"m21","params":[{"y":945,"x":374}],"method":"field.pick","msg":"method"} # this is for chest

# {"params":[],"id":"m10","method":"battle.teleport","msg":"method"}
# {"params":[{"battleId":"a4e9d57f-57c7-5a40-a9bf-d82f0afa9591"}],"id":"m24","method":"battle.items","msg":"method"}
# {"params":[],"id":"m25","method":"user.money","msg":"method"}
# {"params":[{"battleId":"a4e9d57f-57c7-5a40-a9bf-d82f0afa9591"}],"id":"m26","method":"battle_user.top","msg":"method"}
# {"params":[{}],"id":"m27","method":"battle.exit","msg":"method"}
# {"name":"users.current","params":[{"fields":["money","score"]}],"id":"s10","msg":"sub"} # maybe...
# {"params":[],"id":"m28","method":"battle_user.progress","msg":"method"}


# {"msg":"method","id":"m7","params":[{"type":"red_gem","from":2,"to":0}],"method":"user_item.move"}
# {"id":"m16","params":[{"type":"blue_gem","slot":0}],"method":"user_item.sell","msg":"method"}
# {"id":"m18","params":[{"type":"blue_gem","to":0,"from":1}],"method":"user_item.move","msg":"method"}

# {"msg":"method","id":"m15","params":[{"type":"skill_upgrade_time"}],"method":"user.get_adv_bonus"}
# {"msg":"added","collection":"notifications","id":"55d06c23-df33-5ac9-9dda-cffc8288b264","fields":{"type":"enhancement","value":{"type":"upgrade_cost","level":2}}}
# {"msg":"method","id":"m17","params":[{"notificationId":"55d06c23-df33-5ac9-9dda-cffc8288b264"}],"method":"notification.use"}
# {"msg":"method","id":"m12","params":[{"type":"upgrade_cost"}],"method":"enhancement.buy"}




#     request = {"id": "m%d" % msg_id,
#                "params": [{"version": "2.17.1", "platform": "android"}],
#                "msg": "method",
#                "method": "system.version"}
#
#     request = {"id": "m%d" % msg_id,
#                "params": [
#                    {"name": "", "key": generate_key(g_id),
#                     "id": g_id, "gameService": True}],
#                "msg": "method",
#                "method": "login"}
#
#     request = {"id": "m%d" % msg_id,
#                "params": [],
#                "msg": "method",
#                "method": "system.configuration"}

# TODO IS THIS method NEEDED?
#     request = {"id": "m%d" % msg_id,
#                "params": [],
#                "msg": "method",
#                "method": "enhancement.my"}

#     request = {"id": "m%d" % msg_id,
#                "params": [{"range": 1}],
#                "msg": "method",
#                "method": "user.division"}
#
#     request = {"id": "m%d" % msg_id,
#                "params": [],
#                "msg": "method",
#                "method": "system.deployment"}

#     request = {"id": "m%d" % msg_id,
#                "params": [],
#                "msg": "method",
#                "method": "user.tooth_available"}

#     request = {"id": "m%d" % msg_id,
#                "params": [{"type":"tooth"}],
#                "msg": "method",
#                "method": "user.get_adv_bonus"}

#     request = {"id": "m%d" % msg_id,
#                "params": [{"battleId": battles_data_array['Preset1_1']}],
#                "msg": "method",
#                "method": "battle.enter"}
#
#     request = {"id": "m%d" % msg_id,
#                "params": [current_map_info['coords']],
#                # "params": [{"y":1009,"x":100}],
#                "msg": "method",
#                "method": "battle.move"}


def simulate_m_request(ws, method, params=None):
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
    json_request = json.dumps(request)
    init_request(string_id, json_request)
    # ws.send(json_request)


def init_request(string_id, json_request):
    request_queue.put([string_id,json_request])
    send_next_request()



def send_next_request():
    global process_request, request_queue
    if process_request is None:
        if not request_queue.empty():
            req = request_queue.get()
            print(">>> %s: %s" % (req[0], req[1]))
            process_request = req[0]
            sweeperSocket.send(req[1])
        else:
            check_is_needed_solving()



def simulate_sub_request(ws, name, params=None):
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
    print(">>> %s: %s" % (string_id, json_request))
    ws.send(json_request)


def simulate_unsub_request(ws, sub_string_id):
    request = {"id": sub_string_id,
               "msg": "unsub"}
    json_request = json.dumps(request)
    print(">>> unsub %s: %s" % (sub_string_id, json_request))
    ws.send(json_request)


def on_message(ws, message):
    parse_message(message, ws)


def on_error(ws, error):
    print(error)
    pass


def on_close(ws):
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


def move_on_map(x, y):
    if sweeperSocket is not None and 'coords' in current_map_info:
        new_coords = current_map_info['coords']
        new_coords['x'] += x
        new_coords['y'] += y
        simulate_m_request(sweeperSocket, "battle.move", new_coords)


def get_available_gem_space(map_item):
    key_find = map_item['key']
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
        if min_value > map_item['rating']:
            return -1
        elif items_data_array[min_element][1] is not None:
            sell_gem(min_element)
        return int(min_element[-1])



def sell_gem(element):
    gem_type = element[0:-1]
    slot = int(element[-1])
    simulate_m_request(sweeperSocket, "user_item.sell", params={"type":gem_type,"slot":slot})



def pick_on_map(x, y):
    if sweeperSocket is not None and 'coords' in current_map_info:
        to_delete_item = None
        for item in current_map_item_info:
            if item[0] == x and item[1] == y:
                if item[2]['userId'] == login_data_array['profile_id']:
                    if 'gem' in item[2]['key']:
                        slot = get_available_gem_space(item[2])
                        if slot == -1:
                            # in case if gem cheap - sell it
                            simulate_m_request(sweeperSocket,"field.sell", params={"y":y,"x":x})
                        else:
                            simulate_m_request(sweeperSocket,"field.pick", params={"y":y,"x":x,"slot":slot})
                        to_delete_item = item
                    else:
                        simulate_m_request(sweeperSocket,"field.pick", params={"y":y,"x":x})
                        to_delete_item = item
        if to_delete_item is not None:
            current_map_item_info.remove(to_delete_item)
            previous_item_info.insert(0, to_delete_item)
            if len(previous_item_info) > 5:
                previous_item_info.pop()

def flag_on_map(x, y):
    if sweeperSocket is not None and 'coords' in current_map_info:
        simulate_m_request(sweeperSocket,"field.flag", params={"y":y,"x":x})

def open_on_map(x, y):
    if sweeperSocket is not None and 'coords' in current_map_info:
        simulate_m_request(sweeperSocket,"field.open", params={"y":y,"x":x})

def teleport():
    if sweeperSocket is not None and 'coords' in current_map_info:
        simulate_m_request(sweeperSocket,"battle.teleport")

sweeper_width = 38
sweeper_height = 38


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


def do_check(x, y):
    if is_proxy(x, y):
        gold = get_hidden_neighbors(x, y)
        if is_outdated(x, y):
            if len(gold) > 0:
                for g in gold:
                    open_on_map(g[0], g[1])
                    return True
        else:
            dangerous = get_dangerous(x, y)
            if len(gold) + len(dangerous) == sweeper_map[x][y]:
                for g in gold:
                    flag_on_map(g[0], g[1])
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


