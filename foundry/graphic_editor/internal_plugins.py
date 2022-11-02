from __future__ import annotations

from enum import Enum
from json import loads

from PySide6.QtGui import QIcon

from foundry import namespace_path
from foundry.core.drawable import Drawable
from foundry.core.icon import Icon
from foundry.core.namespace import Namespace, TypeHandlerManager, generate_namespace

_icons: Namespace[Icon]


def load_namespace() -> Namespace:
    global _namespace
    global _icons
    with open(str(namespace_path)) as f:
        _namespace = generate_namespace(
            loads(f.read()), validators=TypeHandlerManager.from_managers(Drawable.type_manager, Icon.type_manager)
        )
    _icons = _namespace.children["graphics"].children["common_icons"]
    return _namespace


class CommonIcons(str, Enum):
    SETTINGS = "settings_icon"
    FOLDER = "folder_icon"
    SAVE = "save_icon"
    UNDO = "undo_icon"
    REDO = "redo_icon"
    PLAY = "play_icon"
    ZOOM_IN = "zoom_in_icon"
    ZOOM_OUT = "zoom_out_icon"
    HELP = "help_icon"

    @classmethod
    def to_icon(cls, icon: CommonIcons) -> QIcon:
        return _icons[icon]
