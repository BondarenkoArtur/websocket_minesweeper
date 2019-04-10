import json
import os
from enum import Enum


class ConfigHandler:
    default_settings = {'UI': 'cli',
                        'FPS': 50}

    def __init__(self):
        self.settings = None
        if not os.path.exists(os.path.join(os.getcwd(), 'config.json')):
            self.set_settings(self.default_settings)
        self.reload_settings()

    def reload_settings(self):
        self.settings = self.read_settings()

    def get_setting(self, setting):
        if setting in self.settings:
            return self.settings[setting]
        else:
            return None

    @staticmethod
    def read_settings():
        with open('config.json', 'r') as settings_file:
            return json.load(settings_file)

    @staticmethod
    def set_settings(settings):
        with open('config.json', 'w') as settings_file:
            json.dump(settings, settings_file)


class UI(Enum):
    TUI = 'tui'
    GUI = 'gui'
    CLI = 'cli'
