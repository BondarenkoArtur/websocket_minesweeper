import time

from config.config_handler import ConfigHandler, UI
from network.network_handler import NetworkHandler

if __name__ == '__main__':
    network = NetworkHandler()

    config = ConfigHandler()
    ui_setting = config.get_setting('UI')

    if ui_setting == UI.CLI.value:

        from ui.cli import CLIHandler

        ui = CLIHandler()

    elif ui_setting == UI.TUI.value:

        from ui.tui import TUIHandler

        ui = TUIHandler()

    elif ui_setting == UI.GUI.value:

        from ui.gui import GUIHandler

        ui = GUIHandler()

    else:
        raise Exception("Unknown UI selected")

    network.set_ui_listener(ui.get_listener())
    network.set_google_id(config.get_setting('g_id'))
    network.set_name(config.get_setting('name'))

    fps = config.get_setting('FPS')
    if fps != 0:
        fps = 1 / fps

    while ui.is_running():
        time.sleep(fps)
