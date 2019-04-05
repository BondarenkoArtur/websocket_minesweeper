import os
import sys
from datetime import datetime
from pprint import pformat

import pygame
from pygame.locals import *

from config_parser import get_settings
from image_exporter import export_image
from local_data import login_data_array, counts_data_array, items_data_array, \
    current_map_info, current_map_item_info, \
    sweeper_map, bot_on, previous_item_info, enhancements_array, \
    current_map_all_item_info
from main import run_ws, move_on_map, open_on_map, flag_on_map, \
    switch_solving, print_all_data, pick_on_map, teleport, switch_debug

# INPUT
LEFT_CLICK = 1
MIDDLE_CLICK = 2
RIGHT_CLICK = 3

LIGHTGRAY = (225, 225, 225)
DARKGRAY = (160, 160, 160)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

BGCOLOR = LIGHTGRAY
TEXTCOLOR = BLACK
HIGHLIGHTCOLOR = DARKGRAY
RESETBGCOLOR = LIGHTGRAY

minesweeper = None

class Minesweeper:
    def __init__(self):
        if not pygame.display.get_init():
            pygame.display.init()
        if not pygame.font.get_init():
            pygame.font.init()
        pygame.display.set_caption('Minesweeper')

        self.clock = pygame.time.Clock()

        self.settings = get_settings()

        # Calculating window sizes
        self._BOXSIZE = self.settings['BOXSIZE']
        self._WINDOW_WIDTH = self.settings['WINDOW_WIDTH']
        self._WINDOW_HEIGHT = self.settings['WINDOW_HEIGHT']
        self._GAP = self.settings['GAP']
        if self._WINDOW_WIDTH > self._WINDOW_HEIGHT:
            self.FIELD_SIZE = (self._WINDOW_HEIGHT - self._GAP * 2) // self._BOXSIZE
            self._YMARGIN = (self._WINDOW_HEIGHT - self._GAP * 2) % self._BOXSIZE // 2 + self._GAP
            self._XMARGIN = self._WINDOW_WIDTH - self.FIELD_SIZE * self._BOXSIZE - self._YMARGIN
        else:
            self.FIELD_SIZE = (self._WINDOW_WIDTH - self._GAP * 2) // self._BOXSIZE
            self._XMARGIN = (self._WINDOW_WIDTH - self._GAP * 2) % self._BOXSIZE // 2 + self._GAP
            self._YMARGIN = self._WINDOW_HEIGHT - self.FIELD_SIZE * self._BOXSIZE - self._XMARGIN
        self._FONTTYPE = self.settings['FONTTYPE']
        self._FONTSIZE = self.settings['FONTSIZE']

        # load GUI
        self._display_surface = pygame.display.set_mode(
            (self._WINDOW_WIDTH, self._WINDOW_HEIGHT))
        self._BASICFONT = pygame.font.SysFont(self._FONTTYPE, self._FONTSIZE)
        #         self._RESET_SURF, self._RESET_RECT = self.draw_button('RESET', TEXTCOLOR, RESETBGCOLOR, WINDOWWIDTH/2, 50)
        self._images = {
            '0': pygame.transform.scale(
                pygame.image.load(os.path.join('media', '0.png')),
                (self._BOXSIZE, self._BOXSIZE)),
            '1': pygame.transform.scale(
                pygame.image.load(os.path.join('media', '1.png')),
                (self._BOXSIZE, self._BOXSIZE)),
            '2': pygame.transform.scale(
                pygame.image.load(os.path.join('media', '2.png')),
                (self._BOXSIZE, self._BOXSIZE)),
            '3': pygame.transform.scale(
                pygame.image.load(os.path.join('media', '3.png')),
                (self._BOXSIZE, self._BOXSIZE)),
            '4': pygame.transform.scale(
                pygame.image.load(os.path.join('media', '4.png')),
                (self._BOXSIZE, self._BOXSIZE)),
            '5': pygame.transform.scale(
                pygame.image.load(os.path.join('media', '5.png')),
                (self._BOXSIZE, self._BOXSIZE)),
            '6': pygame.transform.scale(
                pygame.image.load(os.path.join('media', '6.png')),
                (self._BOXSIZE, self._BOXSIZE)),
            '7': pygame.transform.scale(
                pygame.image.load(os.path.join('media', '7.png')),
                (self._BOXSIZE, self._BOXSIZE)),
            '8': pygame.transform.scale(
                pygame.image.load(os.path.join('media', '8.png')),
                (self._BOXSIZE, self._BOXSIZE)),
            'hidden': pygame.transform.scale(
                pygame.image.load(os.path.join('media', 'hidden.png')),
                (self._BOXSIZE, self._BOXSIZE)),
            'flag': pygame.transform.scale(
                pygame.image.load(os.path.join('media', 'flag.png')),
                (self._BOXSIZE, self._BOXSIZE)),
            'wall': pygame.transform.scale(
                pygame.image.load(os.path.join('media', 'wall.png')),
                (self._BOXSIZE, self._BOXSIZE)),
            'mine': pygame.transform.scale(
                pygame.image.load(os.path.join('media', 'mine.png')),
                (self._BOXSIZE, self._BOXSIZE)),
            'null': pygame.transform.scale(
                pygame.image.load(os.path.join('media', 'null.png')),
                (self._BOXSIZE, self._BOXSIZE)),
            'empty': pygame.transform.scale(
                pygame.image.load(os.path.join('media', 'empty.png')),
                (self._BOXSIZE, self._BOXSIZE)),
            'bag': pygame.transform.scale(
                pygame.image.load(os.path.join('media', 'bag.png')),
                (self._BOXSIZE, self._BOXSIZE)),
            'opened': pygame.transform.scale(
                pygame.image.load(os.path.join('media', 'opened.png')),
                (self._BOXSIZE, self._BOXSIZE)),
        }

    def get_image(self, image_id):
        if image_id == -10:
            return self._images.get('empty')
        if image_id == -9:
            return self._images.get('bag')
        if image_id == -8:
            return self._images.get('opened')
        elif image_id == -1:
            return self._images.get('hidden')
        elif 0 <= image_id < 9:
            return self._images.get(str(image_id))
        elif image_id == 9:
            return self._images.get('wall')
        elif image_id == 10:
            return self._images.get('flag')
        elif image_id == 11:
            return self._images.get('mine')
        else:
            return self._images.get('null')


    def draw_field(self):
        """Draws field GUI"""
        self._display_surface.fill(BGCOLOR)

        if 'coords' in current_map_info:
            mid_x = current_map_info['coords']['x']
            mid_y = current_map_info['coords']['y']

            min_x = mid_x - self.FIELD_SIZE // 2
            min_y = mid_y - self.FIELD_SIZE // 2
            max_x = mid_x + self.FIELD_SIZE // 2
            max_y = mid_y + self.FIELD_SIZE // 2

            for x in range(min_x, max_x):
                for y in range(min_y, max_y):
                    if 0 <= x < 2000 and 0 <= y < 2000:
                        left, top = self.get_left_top_xy(x - min_x, y - min_y)
                        if sweeper_map[x][y] != -10:
                            self._display_surface.blit(
                                self.get_image(sweeper_map[x][y]),
                                (left, top))

            min_x = self.FIELD_SIZE // 2 - 58 // 2
            min_y = self.FIELD_SIZE // 2 - 58 // 2

            left, top = self.get_left_top_xy(min_x, min_y)
            pygame.draw.rect(self._display_surface, BLACK,
                             (left, top, self._BOXSIZE * 58, self._BOXSIZE * 58), 1)

    # todo visualize current and next steps

    def draw_ui(self):
        """Draws some text"""
        # TODO make that all stuff better
        margin = 0
        if 'fields' in login_data_array:
            text = ""
            if 'profile' in login_data_array:
                text += login_data_array['profile']['name'] + "   "
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
            self._display_surface.blit(textobj, (self._XMARGIN - textobj.get_width(), 0))
        if 'count' in counts_data_array:
            text = "Current online: %d" % counts_data_array['count']
            margin = self.append_text_on_screen(text, margin, (0, 0, 255))
        if 'divisionType' in counts_data_array:
            text = "League: %s %d" % (counts_data_array['divisionType']['league'], counts_data_array['divisionType']['number'])
            # text = pformat(counts_data_array['divisionType'])
            margin = self.append_text_on_screen(text, margin, (100, 100, 0))
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
        if 'current' in enhancements_array:
            text = "Current enhancements:"
            margin = self.append_text_on_screen(text, margin, (0, 100, 150))
            for cur_enh in enhancements_array['current']:
                text = " %s lvl:%d value:%d" % \
                       (cur_enh['type'], cur_enh['level'], cur_enh['value'])
                if 'upgrade' in cur_enh:
                    ts = cur_enh['upgrade']['finishAt']
                    ts /= 1000
                    d1 = datetime.utcfromtimestamp(ts)
                    d2 = datetime.utcnow()
                    d3 = d1 - d2
                    text += " time left: %s" % str(d3)
                    pass
                margin = self.append_text_on_screen(text, margin,
                                                    (0, 100, 150))
        if 'next' in enhancements_array:
            text = "Next enhancements:"
            margin = self.append_text_on_screen(text, margin, (0, 100, 150))
            for next_enh in enhancements_array['next']:
                text = " %s lvl:%d value:%d price:%d" % \
                       (next_enh['type'], next_enh['level'],
                        next_enh['value'], next_enh['price'])
                if 'requirements' in next_enh:
                    for req in next_enh['requirements' ]:
                        if type(req['value']) is dict:
                            text += " R: %s lvl:%s" % (
                            req['value']['type'], req['value']['level'])
                        else:
                            text += " R: %s %d" % \
                                    (req['type'], req['value'])
                margin = self.append_text_on_screen(text, margin,
                                                    (0, 100, 150))


        # todo make showing current status properly on screen
        text = pformat(bot_on)
        self.append_text_on_screen(text, margin, (0, 0, 0))

    def append_text_on_screen(self, text, margin, text_color):
        lines = text.splitlines()
        for i, l in enumerate(lines):
            textobj = self._BASICFONT.render(l, True, text_color)
            self._display_surface.blit(textobj, (0, margin))
            margin += 12
        return margin

    def highlight_box(self, box_x, box_y):
        """Highlight box when mouse hovers over it"""
        left, top = self.get_left_top_xy(box_x, box_y)
        pygame.draw.rect(self._display_surface, HIGHLIGHTCOLOR,
                         (left, top, self._BOXSIZE, self._BOXSIZE), 4)


    def highlight_coordinates(self, mouse_x, mouse_y, box_x, box_y):
        t_col = (0, 0, 0)
        b_col = (255, 255, 255)
        if 'coords' in current_map_info:
            x = current_map_info['coords']['x'] - self.FIELD_SIZE // 2 + box_x
            y = current_map_info['coords']['y'] - self.FIELD_SIZE // 2 + box_y
            text = "%d, %d" % (x, y)
            if sweeper_map[x][y] == -8 or sweeper_map[x][y] == -9:
                item_text = pformat(current_map_all_item_info["%d,%d" % (x, y)])
                margin = mouse_y-10
                lines = item_text.split(' ')
                for i, l in enumerate(lines):
                    margin += 12
                    textobj = self._BASICFONT.render(l, True, t_col, b_col)
                    self._display_surface.blit(textobj, (mouse_x+10, margin))
            textobj = self._BASICFONT.render(text, True, t_col, b_col)
            self._display_surface.blit(textobj, (mouse_x+10, mouse_y-10))


    def highlight_button(self, but_rect):
        """Highlight button when mouse hovers over it"""
        linewidth = 4
        pygame.draw.rect(self._display_surface, HIGHLIGHTCOLOR, (
            but_rect.left - linewidth, but_rect.top - linewidth,
            but_rect.width + 2 * linewidth, but_rect.height + 2 * linewidth),
                         linewidth)


    # def draw_button(self, text, color, bgcolor, center_x, center_y):
    #     """Similar to draw_text but text has bg color and returns obj & rect"""
    #     but_surf = self._BASICFONT.render(text, True, color, bgcolor)
    #     but_rect = but_surf.get_rect()
    #     but_rect.centerx = center_x
    #     but_rect.centery = center_y
    #
    #     return but_surf, but_rect

    @staticmethod
    def terminate():
        """Simple function to exit game"""
        pygame.quit()
        sys.exit()

    # def draw_text(self, text, font, color, surface, x, y):
    #     """Function to easily draw text and also return object & rect pair"""
    #     textobj = font.render(text, True, color)
    #     textrect = textobj.get_rect()
    #     textrect.centerx = x
    #     textrect.centery = y
    #     surface.blit(textobj, textrect)

    def get_left_top_xy(self, box_x, box_y):
        """Get left & top coordinates for drawing mine boxes"""
        left = self._XMARGIN + box_x * self._BOXSIZE
        top = self._YMARGIN + box_y * self._BOXSIZE
        return left, top

    def get_center_xy(self, box_x, box_y):
        """Get center coordinates for drawing mine boxes"""
        center_x = self._XMARGIN + self._BOXSIZE / 2 + box_x * self._BOXSIZE
        center_y = self._YMARGIN + self._BOXSIZE / 2 + box_y * self._BOXSIZE
        return center_x, center_y

    def get_box_at_pixel(self, x, y):
        """Gets coordinates of box at mouse coordinates"""
        for box_x in range(self.FIELD_SIZE):
            for box_y in range(self.FIELD_SIZE):
                left, top = self.get_left_top_xy(box_x, box_y)
                box_rect = pygame.Rect(left, top, self._BOXSIZE, self._BOXSIZE)
                if box_rect.collidepoint(x, y):
                    return box_x, box_y
        return None, None


def update_sweep_map():
    global minesweeper
    minesweeper.draw_field()

def main():
    global minesweeper
    minesweeper = Minesweeper()

    # stores XY of mouse events
    mouse_x = 0
    mouse_y = 0

    while True:
        has_game_ended = False

        # Main game loop
        while not has_game_ended:

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
                        move_on_map(0, -20)
                    elif event.key == K_DOWN:
                        move_on_map(0,20)
                    elif event.key == K_LEFT:
                        move_on_map(-20, 0)
                    elif event.key == K_RIGHT:
                        move_on_map(20, 0)
                    elif event.key == K_z:
                        switch_solving()
                    elif event.key == K_x:
                        print_all_data()
                    elif event.key == K_a:
                        # todo add manual teleport to coords from UI
                        teleport()
                    elif event.key == K_d:
                        switch_debug()
                    elif event.key == K_s:
                        export_image('map.png')
                elif event.type == MOUSEMOTION:
                    mouse_x, mouse_y = event.pos
                elif event.type == MOUSEBUTTONDOWN and 'coords' in current_map_info:
                    if event.button == LEFT_CLICK:
                        mouse_x, mouse_y = event.pos
                        box_x, box_y = minesweeper.get_box_at_pixel(mouse_x,
                                                                    mouse_y)
                        if box_x is not None and box_y is not None:
                            open_on_map(current_map_info['coords'][
                                            'x'] - minesweeper.FIELD_SIZE // 2 + box_x,
                                        current_map_info['coords'][
                                            'y'] - minesweeper.FIELD_SIZE // 2 + box_y)
                    if event.button == MIDDLE_CLICK:
                        mouse_x, mouse_y = event.pos
                        box_x, box_y = minesweeper.get_box_at_pixel(mouse_x,
                                                                    mouse_y)
                        if box_x is not None and box_y is not None:
                            pick_on_map(current_map_info['coords'][
                                            'x'] - minesweeper.FIELD_SIZE // 2 + box_x,
                                        current_map_info['coords'][
                                            'y'] - minesweeper.FIELD_SIZE // 2 + box_y)
                    if event.button == RIGHT_CLICK:
                        mouse_x, mouse_y = event.pos
                        box_x, box_y = minesweeper.get_box_at_pixel(mouse_x,
                                                                    mouse_y)
                        if box_x is not None and box_y is not None:
                            flag_on_map(current_map_info['coords'][
                                            'x'] - minesweeper.FIELD_SIZE // 2 + box_x,
                                        current_map_info['coords'][
                                            'y'] - minesweeper.FIELD_SIZE // 2 + box_y)

            # # Keeps track of chosen squares
            # if len(safe_squares) > 0:
            #     chosen_squares.append(safe_squares)
            #
            # # Saves turn
            # TRAINING = False
            # if TRAINING and chosen_squares_length == len(chosen_squares):
            #     turn = minesweeper.save_turn()
            #
            # # Apply game changes
            # if not game_over:
            #     for x, y in flagged_squares:
            #         minesweeper.toggle_flag_box(x, y)
            #
            #     for x, y in safe_squares:
            #         game_over = minesweeper.reveal_box(x, y)

            # # Check if reset box is clicked
            # if minesweeper._RESET_RECT.collidepoint(mouse_x, mouse_y):
            #     minesweeper.highlight_button(minesweeper._RESET_RECT)
            #     if mouse_clicked:
            #         minesweeper.new_game()
            #         has_game_ended = True

            # Highlight unrevealed box
            box_x, box_y = minesweeper.get_box_at_pixel(mouse_x, mouse_y)
            if box_x is not None and box_y is not None and \
                            'coords' in current_map_info:
                if not sweeper_map[current_map_info['coords']['x'] \
                            - minesweeper.FIELD_SIZE // 2 + box_x] \
                            [current_map_info['coords']['y'] \
                                - minesweeper.FIELD_SIZE // 2 + box_y] in (-10, 0, 10, 11):
                    minesweeper.highlight_box(box_x, box_y)
                minesweeper.highlight_coordinates(mouse_x, mouse_y, box_x,
                                                  box_y)

            # Update screen, wait clock tick
            pygame.display.update()
            minesweeper.clock.tick(minesweeper.settings['FPS'])


# run code
if __name__ == '__main__':
    run_ws()
    main()
