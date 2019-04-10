from config.config_handler import ConfigHandler, UI
from network.network_handler import NetworkHandler

if __name__ == '__main__':
    network = NetworkHandler()

    config = ConfigHandler()
    ui_setting = config.get_setting('UI')

    if ui_setting == UI.CLI:

        from ui.cli import CLIHandler

        ui = CLIHandler()

    elif ui_setting == UI.TUI:

        from ui.tui import TUIHandler

        ui = TUIHandler()

    elif ui_setting == UI.GUI:

        from ui.gui import GUIHandler

        ui = GUIHandler()

    else:
        raise Exception("Unknown UI selected")
