import json

from qt_material import build_stylesheet

from foundry import default_settings_path

RESIZE_LEFT_CLICK = "LMB"
RESIZE_RIGHT_CLICK = "RMB"


def set_style(theme):
    def wrapped(app):
        app.setStyleSheet(build_stylesheet(theme))

    return wrapped


GUI_STYLE = {
    "DARK AMBER": set_style("dark_amber.xml"),
    "DARK BLUE": set_style("dark_blue.xml"),
    "DARK CYAN": set_style("dark_cyan.xml"),
    "DARK GREEN": set_style("dark_lightgreen.xml"),
    "DARK PINK": set_style("dark_pink.xml"),
    "DARK PURPLE": set_style("dark_purple.xml"),
    "DARK RED": set_style("dark_red.xml"),
    "DARK TEAL": set_style("dark_teal.xml"),
    "DARK YELLOW": set_style("dark_yellow.xml"),
    "LIGHT AMBER": set_style("light_amber.xml"),
    "LIGHT BLUE": set_style("light_blue.xml"),
    "LIGHT CYAN": set_style("light_cyan.xml"),
    "LIGHT GREEN": set_style("light_lightgreen.xml"),
    "LIGHT PINK": set_style("light_pink.xml"),
    "LIGHT PURPLE": set_style("light_purple.xml"),
    "LIGHT RED": set_style("light_red.xml"),
    "LIGHT TEAL": set_style("light_teal.xml"),
    "LIGHT YELLOW": set_style("light_yellow.xml"),
}

SETTINGS = dict()
SETTINGS["instaplay_emulator"] = "fceux"
SETTINGS["instaplay_arguments"] = "%f"
SETTINGS["default_powerup"] = 0
SETTINGS["default_power_has_star"] = False
SETTINGS["default_starting_world"] = 0

SETTINGS["resize_mode"] = RESIZE_LEFT_CLICK
SETTINGS["gui_style"] = ""  # initially blank, since we can't call load_stylesheet until the app is started

SETTINGS["draw_mario"] = True
SETTINGS["draw_jumps"] = False
SETTINGS["draw_grid"] = False
SETTINGS["draw_expansion"] = False
SETTINGS["draw_jump_on_objects"] = True
SETTINGS["draw_items_in_blocks"] = True
SETTINGS["draw_invisible_items"] = True
SETTINGS["draw_autoscroll"] = False
SETTINGS["block_transparency"] = True
SETTINGS["object_scroll_enabled"] = False
SETTINGS["object_tooltip_enabled"] = True


def load_settings():
    if not default_settings_path.exists():
        return

    try:
        with open(str(default_settings_path), "r") as settings_file:
            settings_dict = json.loads(settings_file.read())
    except json.JSONDecodeError:
        return

    SETTINGS.update(settings_dict)


def save_settings():
    with open(str(default_settings_path), "w") as settings_file:
        settings_file.write(json.dumps(SETTINGS, indent=4, sort_keys=True))
