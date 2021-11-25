from typing import Protocol

from PySide6.QtGui import QAction

from foundry.gui.ContextMenu import ContextMenu
from foundry.gui.JumpList import JumpList
from foundry.gui.LevelSizeBar import LevelSizeBar
from foundry.gui.LevelView import LevelView
from foundry.gui.ObjectDropdown import ObjectDropdown
from foundry.gui.ObjectList import ObjectList
from foundry.gui.ObjectToolBar import ObjectToolBar
from foundry.gui.PaletteEditor import PaletteEditor
from foundry.gui.SpinnerPanel import SpinnerPanel
from foundry.gui.WarningList import WarningList


class LevelControlled(Protocol):
    context_menu: ContextMenu
    level_view: LevelView
    spinner_panel: SpinnerPanel
    object_list: ObjectList
    object_dropdown: ObjectDropdown
    level_size_bar: LevelSizeBar
    enemy_size_bar: LevelSizeBar
    side_palette: PaletteEditor
    jump_list: JumpList
    object_toolbar: ObjectToolBar
    warning_list: WarningList
    undo_action: QAction
    redo_action: QAction
    jump_destination_action: QAction
    menu_toolbar_save_action: QAction

    @property
    def safe_to_change(self) -> bool:
        ...

    def update_title(self):
        ...
