from enum import Enum
from json import loads
from os.path import exists
from pathlib import Path

from attr import attrs, field
from pydantic import BaseModel, ValidationError
from qt_material import build_stylesheet

from foundry import default_settings_path, default_styles_path, file_settings_path
from foundry.game.level.util import (
    Level,
    PydanticLevel,
    generate_default_level_information,
    to_pydantic_level,
)


def set_style(theme):
    def wrapped(app):
        app.setStyleSheet(build_stylesheet(theme))

    return wrapped


class ResizeModes(str, Enum):
    """
    A declaration of the possible resize modes accepted by the editor.
    """

    RESIZE_LEFT_CLICK = "LMB"
    RESIZE_RIGHT_CLICK = "RMB"


class GUIStyle(str, Enum):
    """
    A declaration of the possible GUI Styles offered by Foundry.
    """

    DARK_AMBER = "DARK AMBER"
    DARK_BLUE = "DARK BLUE"
    DARK_CYAN = "DARK CYAN"
    DARK_GREEN = "DARK GREEN"
    DARK_PINK = "DARK PINK"
    DARK_PURPLE = "DARK PURPLE"
    DARK_RED = "DARK RED"
    DARK_TEAL = "DARK TEAL"
    DARK_YELLOW = "DARK YELLOW"
    LIGHT_AMBER = "LIGHT AMBER"
    LIGHT_BLUE = "LIGHT BLUE"
    LIGHT_CYAN = "LIGHT CYAN"
    LIGHT_GREEN = "LIGHT GREEN"
    LIGHT_PINK = "LIGHT PINK"
    LIGHT_PURPLE = "LIGHT PURPLE"
    LIGHT_RED = "LIGHT RED"
    LIGHT_TEAL = "LIGHT TEAL"
    LIGHT_YELLOW = "LIGHT YELLOW"


class GUILoader(BaseModel):
    style: dict[GUIStyle, str]

    def load_style(self, style: GUIStyle):
        return set_style(self.style[style])

    class Config:
        # Allow storing the enum as a string
        use_enum_values = True


@attrs(auto_attribs=True, slots=True)
class FileSettings:
    """
    Settings dedicated to a specific file.

    Attributes
    ----------
    levels: list[Level]
        The list of all levels contained inside the file.
    """

    levels: list[Level] = field(factory=generate_default_level_information)


@attrs(auto_attribs=True, slots=True)
class UserSettings:
    """
    The settings for the user for Foundry.

    Attributes
    ----------
    gui_style: GUIStyle
        The style used for the GUI.
    instaplay_emulator: str
        The path to the emulator.
    instaplay_arguments: str
        Any additional arguments passed to the emulator.
    default_powerup: int
        The default powerup to start the player with for testing.
    default_power_has_star: bool
        If the player will start with a star for testing.
    default_starting_world: int
        Which world the player will start in for testing.
    resize_mode: ResizeModes
        Determines how generators can be expanded.
    draw_mario: bool
        Draws the start location of Mario.
    draw_jumps: bool
        Draws the warp indexes of the level.
    draw_grid: bool
        Draws a grid for the level.
    draw_expansion: bool
        Draws the ways generators can expand.
    draw_jump_on_objects: bool
        Draws if an generator will warp the player.
    draw_items_in_blocks: bool
        Draw any items located inside a generator.
    draw_invisible_items: bool
        Draw invisible items.
    draw_autoscroll: bool
        Draws autoscroll routes.
    block_transparency: bool
        Causes generators to be drawn with transparency.
    object_scroll_enabled: bool
        Enables the editing of generators through the use of the scroll wheel.
    object_tooltip_enabled: bool
        Enables tooltips for generators.
    """

    gui_style: GUIStyle = GUIStyle.LIGHT_BLUE
    instaplay_emulator: str = "fceux"
    instaplay_arguments: str = "%f"
    default_powerup: int = 0
    default_power_has_star: bool = False
    default_starting_world: int = 0
    resize_mode: ResizeModes = ResizeModes.RESIZE_LEFT_CLICK
    draw_mario: bool = True
    draw_jumps: bool = False
    draw_grid: bool = False
    draw_expansion: bool = False
    draw_jump_on_objects: bool = True
    draw_items_in_blocks: bool = True
    draw_invisible_items: bool = True
    draw_autoscroll: bool = False
    block_transparency: bool = True
    object_scroll_enabled: bool = False
    object_tooltip_enabled: bool = True


class PydanticFileSettings(BaseModel):
    levels: list[PydanticLevel]


class PydanticUserSettings(BaseModel):
    gui_style: GUIStyle = GUIStyle.LIGHT_BLUE
    instaplay_emulator: str = "fceux"
    instaplay_arguments: str = "%f"
    default_powerup: int = 0
    default_power_has_star: bool = False
    default_starting_world: int = 0
    resize_mode: ResizeModes = ResizeModes.RESIZE_LEFT_CLICK
    draw_mario: bool = True
    draw_jumps: bool = False
    draw_grid: bool = False
    draw_expansion: bool = False
    draw_jump_on_objects: bool = True
    draw_items_in_blocks: bool = True
    draw_invisible_items: bool = True
    draw_autoscroll: bool = False
    block_transparency: bool = True
    object_scroll_enabled: bool = False
    object_tooltip_enabled: bool = True

    def to_user_settings(self) -> UserSettings:
        """
        Generates a user setting.

        Returns
        -------
        UserSettings
            The representation of this instance as a user setting.
        """
        return UserSettings(
            gui_style=self.gui_style,
            instaplay_emulator=self.instaplay_emulator,
            instaplay_arguments=self.instaplay_arguments,
            default_powerup=self.default_powerup,
            default_power_has_star=self.default_power_has_star,
            default_starting_world=self.default_starting_world,
            resize_mode=self.resize_mode,
            draw_mario=self.draw_mario,
            draw_jumps=self.draw_jumps,
            draw_grid=self.draw_grid,
            draw_expansion=self.draw_expansion,
            draw_jump_on_objects=self.draw_jump_on_objects,
            draw_items_in_blocks=self.draw_items_in_blocks,
            draw_invisible_items=self.draw_invisible_items,
            draw_autoscroll=self.draw_autoscroll,
            block_transparency=self.block_transparency,
            object_scroll_enabled=self.object_scroll_enabled,
            object_tooltip_enabled=self.object_tooltip_enabled,
        )

    class Config:
        # Allow storing the enum as a string
        use_enum_values = True


def user_setting_to_json(user_setting: UserSettings, path: str):
    p_user_setting = PydanticUserSettings(
        gui_style=user_setting.gui_style,
        instaplay_emulator=user_setting.instaplay_emulator,
        instaplay_arguments=user_setting.instaplay_arguments,
        default_powerup=user_setting.default_powerup,
        default_power_has_star=user_setting.default_power_has_star,
        default_starting_world=user_setting.default_starting_world,
        resize_mode=user_setting.resize_mode,
        draw_mario=user_setting.draw_mario,
        draw_jumps=user_setting.draw_jumps,
        draw_grid=user_setting.draw_grid,
        draw_expansion=user_setting.draw_expansion,
        draw_jump_on_objects=user_setting.draw_jump_on_objects,
        draw_items_in_blocks=user_setting.draw_items_in_blocks,
        draw_invisible_items=user_setting.draw_invisible_items,
        draw_autoscroll=user_setting.draw_autoscroll,
        block_transparency=user_setting.block_transparency,
        object_scroll_enabled=user_setting.object_scroll_enabled,
        object_tooltip_enabled=user_setting.object_tooltip_enabled,
    )

    with open(path, "w") as settings_file:
        settings_file.write(p_user_setting.json(indent=4))


def to_pydantic_file_settings(file_settings: FileSettings) -> PydanticFileSettings:
    """
    Converts file settings to its pydantic equivelant.

    Parameters
    ----------
    file_settings : FileSettings
        The file settings to convert.

    Returns
    -------
    PydanticFileSettings
        The pydantic equivelant of the file settings provided.
    """
    return PydanticFileSettings(levels=[to_pydantic_level(level) for level in file_settings.levels])


def load_gui_loader() -> GUILoader:
    """
    Generates mappings to load the possible GUI styles.

    Returns
    -------
    GUILoader
        The loader for the GUI styles.
    """
    with open(default_styles_path) as f:
        return GUILoader(style=loads(f.read()))


def load_file_settings(file_id: str) -> FileSettings:
    """
    Attempts to load the file settings for a given file.  If none exists, then the default file settings
    will be utilized instead.

    Parameters
    ----------
    file_id : str
        The file name for the file settings.

    Returns
    -------
    FileSettings
        The file settings that best match the provided file.
    """
    if not exists(file_settings_path / file_id):
        return FileSettings()
    try:
        with open(file_settings_path / file_id) as f:
            return FileSettings([PydanticLevel(**level).to_level() for level in loads(f.read())["levels"]])
    except TypeError:
        # Todo: Probably should add a warning to the user here.
        return FileSettings()


def save_file_settings(file_id: str, file_settings: FileSettings):
    """
    Saves file settings to a file.

    Parameters
    ----------
    file_id : str
        The file to save the settings for.
    file_settings : FileSettings
        The settings to save.
    """
    with open(file_settings_path / file_id, "w") as settings_file:
        settings_file.write(to_pydantic_file_settings(file_settings).json(indent=4))


def load_settings(file_path: Path = default_settings_path) -> UserSettings:
    """
    Provides the user settings.

    Returns
    -------
    UserSettings
        The current user settings.
    """
    try:
        with open(str(file_path)) as settings_file:
            return PydanticUserSettings(**loads(settings_file.read())).to_user_settings()
    except (TypeError, FileNotFoundError, ValidationError):
        return PydanticUserSettings().to_user_settings()


def save_settings(user_settings: UserSettings):
    """
    Saves the user settings to a file.

    Parameters
    ----------
    user_settings : UserSettings
        The user settings to save.
    """
    user_setting_to_json(user_settings, str(default_settings_path))
