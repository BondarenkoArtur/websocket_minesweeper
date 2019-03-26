import os
import random
import sys
from pprint import pformat

import pygame
from pygame.locals import *

from local_data import login_data_array, counts_data_array, items_data_array, \
    battles_data_array, current_map_info, current_map_item_info, \
    sweeper_map, bot_on, previous_item_info

sys.setrecursionlimit(10000)  # 10000 is an example, try with different values

from main import run_ws, move_on_map, open_on_map, flag_on_map, \
    switch_solving, print_all_data, pick_on_map, teleport

FIELDWIDTH, FIELDHEIGHT, MINESTOTAL = (50, 50, 200)

# UI
FPS = 30
BOXSIZE = 8
# BOXSIZE = 16
WINDOWWIDTH = FIELDWIDTH * BOXSIZE + 585
WINDOWHEIGHT = FIELDHEIGHT * BOXSIZE + 20
XMARGIN = int(280 + (WINDOWWIDTH - (FIELDWIDTH * BOXSIZE)) / 2)
YMARGIN = 10

# INPUT
LEFT_CLICK = 1
MIDDLE_CLICK = 2
RIGHT_CLICK = 3

# assertions
assert MINESTOTAL < FIELDHEIGHT * FIELDWIDTH, 'More mines than boxes'
assert BOXSIZE ^ 2 * (
    FIELDHEIGHT * FIELDWIDTH) < WINDOWHEIGHT * WINDOWWIDTH, 'Boxes will not fit on screen'

LIGHTGRAY = (225, 225, 225)
DARKGRAY = (160, 160, 160)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

BGCOLOR = LIGHTGRAY
TEXTCOLOR = BLACK
HIGHLIGHTCOLOR = DARKGRAY
RESETBGCOLOR = LIGHTGRAY

# set up font
FONTTYPE = 'Terminus (TTF)'
FONTSIZE = 12

MINE = 'X'
FLAGGED = -2
HIDDEN = -1

minesweeper = None

class Minesweeper:
    def __init__(self):
        # random.seed(0)  # Seed the RNG for DEBUG purposes
        if not pygame.display.get_init():
            pygame.display.init()
        if not pygame.font.get_init():
            pygame.font.init()
        pygame.display.set_caption('Minesweeper')

        self.clock = pygame.time.Clock()

        # load GUI
        self._display_surface = pygame.display.set_mode(
            (WINDOWWIDTH, WINDOWHEIGHT))
        self._BASICFONT = pygame.font.SysFont(FONTTYPE, FONTSIZE)
        #         self._RESET_SURF, self._RESET_RECT = self.draw_button('RESET', TEXTCOLOR, RESETBGCOLOR, WINDOWWIDTH/2, 50)
        self._images = {
            '0': pygame.transform.scale(
                pygame.image.load(os.path.join('media', '0.png')),
                (BOXSIZE, BOXSIZE)),
            '1': pygame.transform.scale(
                pygame.image.load(os.path.join('media', '1.png')),
                (BOXSIZE, BOXSIZE)),
            '2': pygame.transform.scale(
                pygame.image.load(os.path.join('media', '2.png')),
                (BOXSIZE, BOXSIZE)),
            '3': pygame.transform.scale(
                pygame.image.load(os.path.join('media', '3.png')),
                (BOXSIZE, BOXSIZE)),
            '4': pygame.transform.scale(
                pygame.image.load(os.path.join('media', '4.png')),
                (BOXSIZE, BOXSIZE)),
            '5': pygame.transform.scale(
                pygame.image.load(os.path.join('media', '5.png')),
                (BOXSIZE, BOXSIZE)),
            '6': pygame.transform.scale(
                pygame.image.load(os.path.join('media', '6.png')),
                (BOXSIZE, BOXSIZE)),
            '7': pygame.transform.scale(
                pygame.image.load(os.path.join('media', '7.png')),
                (BOXSIZE, BOXSIZE)),
            '8': pygame.transform.scale(
                pygame.image.load(os.path.join('media', '8.png')),
                (BOXSIZE, BOXSIZE)),
            'hidden': pygame.transform.scale(
                pygame.image.load(os.path.join('media', 'hidden.png')),
                (BOXSIZE, BOXSIZE)),
            'flag': pygame.transform.scale(
                pygame.image.load(os.path.join('media', 'flag.png')),
                (BOXSIZE, BOXSIZE)),
            'wall': pygame.transform.scale(
                pygame.image.load(os.path.join('media', 'wall.png')),
                (BOXSIZE, BOXSIZE)),
            'mine': pygame.transform.scale(
                pygame.image.load(os.path.join('media', 'mine.png')),
                (BOXSIZE, BOXSIZE)),
            'null': pygame.transform.scale(
                pygame.image.load(os.path.join('media', 'null.png')),
                (BOXSIZE, BOXSIZE)),
            'empty': pygame.transform.scale(
                pygame.image.load(os.path.join('media', 'empty.png')),
                (BOXSIZE, BOXSIZE)),
            'bag': pygame.transform.scale(
                pygame.image.load(os.path.join('media', 'bag.png')),
                (BOXSIZE, BOXSIZE)),
        }

        self.database = []
        self.mine_field, self.revealed_boxes, self.flagged_mines = self.new_game()  # , self.game_over

    def new_game(self):
        """Set up mine field data structure, list of all zeros for recursion, and revealed box boolean data structure"""

        # self.game_over = False
        self.mine_field = self.get_random_minefield()
        self.revealed_boxes = self.get_field_with_value(False)
        self.flagged_mines = self.get_field_with_value(False)

        return self.mine_field, self.revealed_boxes, self.flagged_mines  # , self.game_over

    def get_image(self, box_x, box_y):
        if self.flagged_mines[box_x][box_y]:
            return self._images.get('flag')
        if self.revealed_boxes[box_x][box_y]:
            if self.mine_field[box_x][box_y] == MINE:
                return self._images.get('mine')
            else:
                return self._images.get(str(self.mine_field[box_x][box_y]))
        else:
            return self._images.get('hidden')

    def get_custom_image(self, id):
        if id == -10:
            return self._images.get('empty')
        if id == -9:
            return self._images.get('bag')
        elif id == -1:
            return self._images.get('hidden')
        elif 0 <= id < 9:
            return self._images.get(str(id))
        elif id == 9:
            return self._images.get('wall')
        elif id == 10:
            return self._images.get('flag')
        elif id == 11:
            return self._images.get('mine')
        else:
            return self._images.get('null')


    def draw_field(self):
        """Draws field GUI"""
        self._display_surface.fill(BGCOLOR)

        if 'coords' in current_map_info:
            mid_x = current_map_info['coords']['x']
            mid_y = current_map_info['coords']['y']

            min_x = mid_x - FIELDWIDTH // 2
            min_y = mid_y - FIELDHEIGHT // 2
            max_x = mid_x + FIELDWIDTH // 2
            max_y = mid_y + FIELDHEIGHT // 2

            for x in range(min_x, max_x):
                for y in range(min_y, max_y):
                    if 0 <= x < 2000 and 0 <= y < 2000:
                        left, top = self.get_left_top_xy(x - min_x, y - min_y)
                        if sweeper_map[x][y] != -10:
                            self._display_surface.blit(
                                self.get_custom_image(sweeper_map[x][y]),
                                (left, top))

            min_x = FIELDWIDTH // 2 - 38 // 2
            min_y = FIELDHEIGHT // 2 - 38 // 2

            left, top = self.get_left_top_xy(min_x, min_y)
            pygame.draw.rect(self._display_surface, BLACK,
                             (left, top, BOXSIZE * 38, BOXSIZE * 38), 1)

            # for mine in map_info:
            #     if min_x < mine[0] < max_x and min_y < mine[1] < max_y:
            #         left, top = self.get_left_top_xy(mine[0]-min_x, mine[1]-min_y)
            #         if type(mine[2]) is dict :
            #             if mine not in current_map_item_info:
            #                 current_map_item_info.append(mine)
            #             self._display_surface.blit(self._images.get('bag'),
            #                                    (left, top))
            #         else:
            #             self._display_surface.blit(self.get_custom_image(mine[2]),
            #                                    (left, top))

            # for box_x in range(FIELDWIDTH):
            #     for box_y in range(FIELDHEIGHT):
            #         left, top = self.get_left_top_xy(box_x, box_y)
            #         self._display_surface.blit(self.get_custom_image(box_x, box_y),
            #                                    (left, top))

    def draw_ui(self):
        """Draws some text"""
        # TODO make that all stuff better
        margin = 0
        if 'fields' in login_data_array:
            text = login_data_array['fields']['profile']['name'] + "   "
            if 'lives' in login_data_array['fields']:
                text += " Lives: %d" % login_data_array['fields']['lives']
            if 'money' in login_data_array['fields']:
                text += " Money: %d" % login_data_array['fields']['money']
            if 'score' in login_data_array['fields']:
                text += " Score: %d" % login_data_array['fields']['score']
            if 'rank' in login_data_array['fields']:
                text += " Rank: %d" % login_data_array['fields']['rank']
            if 'workbench' in login_data_array['fields']:
                text += " WB: %d" % login_data_array['fields']['workbench']
            # text = pformat(login_data_array)
            margin = self.append_text_on_screen(text, margin, (0, 150, 50))
        if 'coords' in current_map_info:
            text = "X: %d Y: %d" % (current_map_info['coords']['x'], current_map_info['coords']['y'])
            # text = pformat(current_map_info)
            textobj = self._BASICFONT.render(text, True, (150, 0, 150))
            self._display_surface.blit(textobj, (XMARGIN - textobj.get_width(), 0))
        if 'count' in counts_data_array:
            text = "Current online: %d" % counts_data_array['count']
            margin = self.append_text_on_screen(text, margin, (0, 0, 255))
        if 'division' in counts_data_array:
            s_list = sorted(counts_data_array['division'], key=lambda kv: (kv['position']))
            text = "Division: \n %d %d %s \n %d %d %s \n %d %d %s " % \
                   (s_list[0]['position'], s_list[0]['value'], s_list[0]['name'],
                    s_list[1]['position'], s_list[1]['value'], s_list[1]['name'],
                    s_list[2]['position'], s_list[2]['value'], s_list[2]['name'])
            # text = pformat(counts_data_array)
            margin = self.append_text_on_screen(text, margin, (100, 100, 0))
        for map_item in current_map_item_info:
            if 'rating' in map_item[2]:
                text = "Item on map: X: %d Y: %d Key: %s %d" % \
                       (map_item[0], map_item[1], map_item[2]['key'],
                        map_item[2]['rating'])
            elif 'items' in map_item[2]:
                text = "Item on map: X: %d Y: %d Key: %s %s %d" % \
                       (map_item[0], map_item[1], map_item[2]['key'],
                        map_item[2]['items'][0].get('type', 'null'),
                        map_item[2]['items'][0].get('value', 0))
            else:
                text = "Item on map: X: %d Y: %d Key: %s" % \
                       (map_item[0], map_item[1], map_item[2]['key'])
            # text = pformat(current_map_item_info)
            margin = self.append_text_on_screen(text, margin, (150, 0, 255))
        for prev_item in previous_item_info:
            if 'rating' in prev_item[2]:
                text = "Picked item: X: %d Y: %d Key: %s %d" % \
                       (prev_item[0], prev_item[1], prev_item[2]['key'],
                        prev_item[2]['rating'])
            elif 'items' in prev_item[2]:
                text = "Picked item: X: %d Y: %d Key: %s %s %d" % \
                       (prev_item[0], prev_item[1], prev_item[2]['key'],
                        prev_item[2]['items'][0].get('type', 'null'),
                        prev_item[2]['items'][0].get('value', 0))
            else:
                text = "Picked item: X: %d Y: %d Key: %s" % \
                       (prev_item[0], prev_item[1], prev_item[2]['key'])
            # text = pformat(previous_item_info)
            margin = self.append_text_on_screen(text, margin, (100, 0, 200))
        # todo make showing items better on screen
        text = pformat(items_data_array)
        margin = self.append_text_on_screen(text, margin, (150, 0, 0))
        # text = pformat(battles_data_array)
        # margin = self.append_text_on_screen(text, margin, (0, 0, 0))

        # todo make showing current status properly on screen
        text = pformat(bot_on)
        margin = self.append_text_on_screen(text, margin, (0, 0, 0))

    def append_text_on_screen(self, text, margin, color):
        lines = text.splitlines()
        for i, l in enumerate(lines):
            textobj = self._BASICFONT.render(l, True, color)
            self._display_surface.blit(textobj, (0, margin))
            margin += 12
        return margin

    def highlight_box(self, box_x, box_y):
        """Highlight box when mouse hovers over it"""
        left, top = self.get_left_top_xy(box_x, box_y)
        pygame.draw.rect(self._display_surface, HIGHLIGHTCOLOR,
                         (left, top, BOXSIZE, BOXSIZE), 4)


    def highlight_coordinates(self, mouse_x, mouse_y, box_x, box_y):
        if 'coords' in current_map_info:
            text = pformat(
                [current_map_info['coords']['x'] - FIELDWIDTH // 2 + box_x,
                 current_map_info['coords']['y'] - FIELDHEIGHT // 2 + box_y])
            textobj = self._BASICFONT.render(text, True, (0, 0, 0),
                                             (255, 255, 255))
            self._display_surface.blit(textobj, (mouse_x, mouse_y-10))


    def highlight_button(self, butRect):
        """Highlight button when mouse hovers over it"""
        linewidth = 4
        pygame.draw.rect(self._display_surface, HIGHLIGHTCOLOR, (
            butRect.left - linewidth, butRect.top - linewidth,
            butRect.width + 2 * linewidth, butRect.height + 2 * linewidth),
                         linewidth)

    def is_game_won(self):
        """Checks if player has revealed all boxes"""
        not_mine_count = 0

        # todo fix for large remove False
        return False

        for box_x in range(FIELDWIDTH):
            for box_y in range(FIELDHEIGHT):
                if self.revealed_boxes[box_x][box_y] == True:
                    if self.mine_field[box_x][box_y] != MINE:
                        not_mine_count += 1

        if not_mine_count >= (FIELDWIDTH * FIELDHEIGHT) - MINESTOTAL:
            return True
        else:
            return False

    def _save_turn(self):
        info = self.available_info()

        score = 0
        for col in info:
            score += sum(i != MINE and i != -1 for i in col)

        self.database.append({
            "turn": info,
            "score": score,
        })

    #         print(self.database[-1])

    def save_turn(self):
        # Saves input for ANN training
        turn = []
        for i in range(FIELDWIDTH):
            for j in range(FIELDHEIGHT):
                square = []
                if self.revealed_boxes[i][j]:
                    square.append(self.mine_field[i][j])
                else:
                    square.append(-1)
                turn.append(square)
        return turn

    def available_info(self):
        info = []

        for x in range(len(self.mine_field)):
            line = []
            for y in range(len(self.mine_field[x])):
                if self.flagged_mines[x][y]:
                    line.append(FLAGGED)
                else:
                    try:
                        line.append(int(self.mine_field[x][y]) if
                                    self.revealed_boxes[x][y] else HIDDEN)
                    except:
                        line.append('X')
            info.append(line)

        # self.debug_field(info, 'info')
        return info

    def toggle_flag_box(self, x, y):
        """Toggles if mine box is flagged"""
        if not self.flagged_mines[x][y] and not self.revealed_boxes[x][y]:
            self.flagged_mines[x][y] = True
        else:
            self.flagged_mines[x][y] = False

    def reveal_box(self, x, y):
        """Reveals box clicked"""
        self.game_over = False
        self.revealed_boxes[x][y] = True

        if self.is_game_won():
            self.game_over = True

            # when 0 is revealed, show relevant boxes
        if self.mine_field[x][y] == 0:
            self.reveal_empty_squares(x, y)

        # when mine is revealed, show mines
        if self.mine_field[x][y] == MINE:
            self.show_mines()
            self.game_over = True

        return self.game_over

    def reveal_empty_squares(self, box_x, box_y):  # , zero_list_xy=[]):
        """Modifies revealed_boxes data structure if chosen box_x & box_y is 0
        Shows all boxes using recursion
        """
        self.revealed_boxes[box_x][box_y] = True

        if box_x > 0 and box_y > 0:
            if self.revealed_boxes[box_x - 1][box_y - 1] == False:
                self.reveal_box(box_x - 1, box_y - 1)

        if box_y > 0:
            if self.revealed_boxes[box_x][box_y - 1] == False:
                self.reveal_box(box_x, box_y - 1)

        if box_x < FIELDWIDTH - 1 and box_y > 0:
            if self.revealed_boxes[box_x + 1][box_y - 1] == False:
                self.reveal_box(box_x + 1, box_y - 1)

        if box_x > 0:
            if self.revealed_boxes[box_x - 1][box_y] == False:
                self.reveal_box(box_x - 1, box_y)

        if box_x < FIELDWIDTH - 1:
            if self.revealed_boxes[box_x + 1][box_y] == False:
                self.reveal_box(box_x + 1, box_y)

        if box_x > 0 and box_y < FIELDHEIGHT - 1:
            if self.revealed_boxes[box_x - 1][box_y + 1] == False:
                self.reveal_box(box_x - 1, box_y + 1)

        if box_y < FIELDHEIGHT - 1:
            if self.revealed_boxes[box_x][box_y + 1] == False:
                self.reveal_box(box_x, box_y + 1)

        if box_x < FIELDWIDTH - 1 and box_y < FIELDHEIGHT - 1:
            if self.revealed_boxes[box_x + 1][box_y + 1] == False:
                self.reveal_box(box_x + 1, box_y + 1)

    def show_mines(self):
        """Modifies revealed_boxes data structure if chosen box_x & box_y is X"""
        for i in range(FIELDWIDTH):
            for j in range(FIELDHEIGHT):
                if self.mine_field[i][j] == MINE:
                    self.revealed_boxes[i][j] = True

    def draw_button(self, text, color, bgcolor, center_x, center_y):
        """Similar to draw_text but text has bg color and returns obj & rect"""
        but_surf = self._BASICFONT.render(text, True, color, bgcolor)
        but_rect = but_surf.get_rect()
        but_rect.centerx = center_x
        but_rect.centery = center_y

        return but_surf, but_rect

    def is_there_mine(self, field, x, y):
        """Checks if mine is located at specific box on field"""
        return field[x][y] == MINE

    def place_numbers(self, field):
        """Places numbers in FIELDWIDTH x FIELDHEIGHT data structure"""
        for x in range(FIELDWIDTH):
            for y in range(FIELDHEIGHT):
                if not self.is_there_mine(field, x, y):
                    field[x][y] = [
                        field[neighbour_x][neighbour_y]
                        for neighbour_x, neighbour_y in
                        self.get_neighbour_squares([x, y])
                    ].count(MINE)

    def get_random_minefield(self):
        """Places mines in FIELDWIDTH x FIELDHEIGHT data structure"""
        field = self.get_field_with_value(0)
        mine_count = 0
        xy = []
        while mine_count < MINESTOTAL:
            x = random.randint(0, FIELDWIDTH - 1)
            y = random.randint(0, FIELDHEIGHT - 1)
            if [x, y] not in xy:
                xy.append([x, y])
                field[x][y] = MINE
                mine_count += 1

        self.place_numbers(field)
        return field

    def get_field_with_value(self, value):
        """Returns FIELDWIDTH x FIELDHEIGHT data structure completely filled with VALUE"""
        revealed_boxes = []
        for _ in range(FIELDWIDTH):
            revealed_boxes.append([value] * FIELDHEIGHT)
        return revealed_boxes

    def terminate(self):
        """Simple function to exit game"""
        pygame.quit()
        sys.exit()

    def draw_text(self, text, font, color, surface, x, y):
        """Function to easily draw text and also return object & rect pair"""
        textobj = font.render(text, True, color)
        textrect = textobj.get_rect()
        textrect.centerx = x
        textrect.centery = y
        surface.blit(textobj, textrect)

    def get_left_top_xy(self, box_x, box_y):
        """Get left & top coordinates for drawing mine boxes"""
        left = XMARGIN + box_x * BOXSIZE
        top = YMARGIN + box_y * BOXSIZE
        return left, top

    def get_center_xy(self, box_x, box_y):
        """Get center coordinates for drawing mine boxes"""
        center_x = XMARGIN + BOXSIZE / 2 + box_x * BOXSIZE
        center_y = YMARGIN + BOXSIZE / 2 + box_y * BOXSIZE
        return center_x, center_y

    def get_box_at_pixel(self, x, y):
        """Gets coordinates of box at mouse coordinates"""
        for box_x in range(FIELDWIDTH):
            for box_y in range(FIELDHEIGHT):
                left, top = self.get_left_top_xy(box_x, box_y)
                boxRect = pygame.Rect(left, top, BOXSIZE, BOXSIZE)
                if boxRect.collidepoint(x, y):
                    return (box_x, box_y)
        return (None, None)

    def debug_field(self, board, title=None):
        """Prints minefield for debug purposes"""
        if title:
            print(title)
        for y in range(len(board)):
            print([board[x][y] for x in range(len(board[y]))])
        print()

    def get_neighbour_squares(self, square, min_x=0, max_x=FIELDWIDTH - 1,
                              min_y=0, max_y=FIELDHEIGHT - 1):
        """Returns list of squares that are adjacent to specified square"""
        neighbours = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                neighbours.append([square[0] + i, square[1] + j])
        neighbours.remove(square)

        if min_x is not None:
            neighbours = [item for item in neighbours if item[0] >= min_x]

        if max_x is not None:
            neighbours = [item for item in neighbours if item[0] <= max_x]

        if min_y is not None:
            neighbours = [item for item in neighbours if item[1] >= min_y]

        if max_y is not None:
            neighbours = [item for item in neighbours if item[1] <= max_y]

        return neighbours

    def get_uncertain_neighbours(self, square, available_info):
        """Returns adjacent squares that are uncertain (flagged not included)"""
        hidden_squares = []
        for x, y in self.get_neighbour_squares(square):
            if available_info[x][y] == HIDDEN:
                hidden_squares.append([x, y])
        return hidden_squares

    def get_flagged_neighbours(self, square, available_info):
        """Returns adjacent squares that have been flagged"""
        flagged_squares = []
        for x, y in self.get_neighbour_squares(square):
            if available_info[x][y] == FLAGGED:
                flagged_squares.append([x, y])
        return flagged_squares

    def get_hidden_neighbours(self, square, available_info):
        """Returns adjacent squares that have not been clicked yet"""
        hidden = self.get_uncertain_neighbours(square, available_info)
        hidden.extend(self.get_flagged_neighbours(square, available_info))
        return hidden

    def get_AI_flagged_squares(self, available_info):
        """Returns list of squares that are sure to contain mines"""
        flagged_squares = []

        for x, y in [(x, y) for x in range(len(available_info)) for y in
                     range(len(available_info[x]))]:
            neighbours = self.get_hidden_neighbours([x, y], available_info)
            if available_info[x][y] == len(neighbours):
                unflagged = [square for square in neighbours
                             if
                             available_info[square[0]][square[1]] == HIDDEN and
                             square not in flagged_squares]
                flagged_squares.extend(unflagged)

        return flagged_squares

    def get_AI_safe_squares(self, available_info, guess=False):
        """Returns list of squares that are sure to NOT contain mines"""
        safe_squares = []

        for x in range(FIELDWIDTH):
            for y in range(FIELDHEIGHT):
                flagged = self.get_flagged_neighbours([x, y], available_info)
                if available_info[x][y] == len(flagged):
                    safe_squares.extend(
                        self.get_uncertain_neighbours([x, y], available_info))

        if not safe_squares and guess:
            safe_squares.append([random.choice(range(FIELDWIDTH)),
                                 random.choice(range(FIELDHEIGHT))])

        return safe_squares




def update_sweep_map():
    global minesweeper
    minesweeper.draw_field()

def main():
    tries = 0
    plays = 0
    db_good = []
    db_bad = []
    global minesweeper
    minesweeper = Minesweeper()

    # stores XY of mouse events
    mouse_x = 0
    mouse_y = 0

    while True:
        has_game_ended = False
        game_over = False

        minesweeper.new_game()

        tries += 1

        # For random training
        chosen_squares = []
        chosen_squares_length = 1

        # Main game loop
        while not has_game_ended:
            # Initialize variables
            mouse_clicked = False
            safe_squares = []
            flagged_squares = []
            new_position = False  # For random training

            # Draw screen
            minesweeper.draw_field()
            minesweeper.draw_ui()

            # Get player input
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and (
                                event.key == K_ESCAPE or event.key == K_q)):
                    minesweeper.terminate()
                elif event.type == KEYDOWN:
                    if event.key == K_UP:
                        move_on_map(0, -10)
                    elif event.key == K_DOWN:
                        move_on_map(0,10)
                    elif event.key == K_LEFT:
                        move_on_map(-10, 0)
                    elif event.key == K_RIGHT:
                        move_on_map(10, 0)
                    elif event.key == K_z:
                        switch_solving()
                    elif event.key == K_x:
                        print_all_data()
                    elif event.key == K_a:
                        # todo add manual teleport to coords from UI
                        teleport()
                elif event.type == MOUSEMOTION:
                    mouse_x, mouse_y = event.pos
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == LEFT_CLICK:
                        mouse_x, mouse_y = event.pos
                        mouse_clicked = True
                        box_x, box_y = minesweeper.get_box_at_pixel(mouse_x,
                                                                    mouse_y)


                        if box_x is not None and box_y is not None:
                            open_on_map(current_map_info['coords'][
                                            'x'] - FIELDWIDTH // 2 + box_x,
                                        current_map_info['coords'][
                                            'y'] - FIELDHEIGHT // 2 + box_y)
                    if event.button == MIDDLE_CLICK:
                        mouse_x, mouse_y = event.pos
                        box_x, box_y = minesweeper.get_box_at_pixel(mouse_x,
                                                                    mouse_y)
                        if box_x is not None and box_y is not None:
                            pick_on_map(current_map_info['coords'][
                                            'x'] - FIELDWIDTH // 2 + box_x,
                                        current_map_info['coords'][
                                            'y'] - FIELDHEIGHT // 2 + box_y)
                    if event.button == RIGHT_CLICK:
                        mouse_x, mouse_y = event.pos
                        box_x, box_y = minesweeper.get_box_at_pixel(mouse_x,
                                                                    mouse_y)
                        if box_x is not None and box_y is not None:
                            flag_on_map(current_map_info['coords'][
                                            'x'] - FIELDWIDTH // 2 + box_x,
                                        current_map_info['coords'][
                                            'y'] - FIELDHEIGHT // 2 + box_y)

            # Keeps track of chosen squares
            if len(safe_squares) > 0:
                chosen_squares.append(safe_squares)

            # Saves turn
            TRAINING = False
            if TRAINING and chosen_squares_length == len(chosen_squares):
                turn = minesweeper.save_turn()

            # Apply game changes
            if not game_over:
                for x, y in flagged_squares:
                    minesweeper.toggle_flag_box(x, y)

                for x, y in safe_squares:
                    game_over = minesweeper.reveal_box(x, y)

            # # Check if reset box is clicked
            # if minesweeper._RESET_RECT.collidepoint(mouse_x, mouse_y):
            #     minesweeper.highlight_button(minesweeper._RESET_RECT)
            #     if mouse_clicked:
            #         minesweeper.new_game()
            #         has_game_ended = True

            # Highlight unrevealed box
            box_x, box_y = minesweeper.get_box_at_pixel(mouse_x, mouse_y)
            if box_x is not None and box_y is not None and not \
                    minesweeper.revealed_boxes[box_x][box_y]:
                minesweeper.highlight_box(box_x, box_y)
                minesweeper.highlight_coordinates(mouse_x, mouse_y, box_x, box_y)

            # Update screen, wait clock tick
            pygame.display.update()
            minesweeper.clock.tick(FPS)


# run code
if __name__ == '__main__':
    run_ws()
    main()
