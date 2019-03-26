# todo make this storage better

login_data_array = {}

counts_data_array = {}

current_map_info = {}
current_map_item_info = []
previous_item_info = []

items_data_array = {}
battles_data_array = {}

battles_full_data_array = {}

bot_on = [0]


SIZE=2000
sweeper_map = []
for i in range (0, SIZE):
    new = []
    for j in range (0, SIZE):
            new.append(-10)
    sweeper_map.append(new)

