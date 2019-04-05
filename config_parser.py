import json
import os

# Default settings
default_settings = {'FPS': 30,
                    'BOXSIZE': 8,
                    # 'BOXSIZE': 16,
                    'WINDOW_WIDTH': 1280,
                    'WINDOW_HEIGHT': 720,
                    'GAP': 0,
                    'FONTTYPE': 'Terminus (TTF)',
                    'FONTSIZE': 12,
                    }

def get_settings():
    if os.path.exists(os.path.join(os.getcwd(), 'config.json')):
        with open('config.json', 'r') as settings_file:
            return json.load(settings_file)
    else:
        set_settings(default_settings)
        return default_settings


def set_settings(settings):
    with open('config.json', 'w') as settings_file:
        json.dump(settings, settings_file)


if __name__ == "__main__":
    # todo remove set defaults
    set_settings(default_settings)
    settings = get_settings()
    input()