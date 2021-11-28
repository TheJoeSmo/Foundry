from json import loads
from typing import Optional

from PySide6.QtWidgets import QWidget

from foundry import jump_creator_flags_path
from foundry.gui.HeaderEditor import HeaderEditor
from foundry.gui.LevelView import LevelView, undoable
from foundry.gui.util import setup_layout


class JumpCreator(QWidget):
    """
    A menu item used to create and modify jumps inside the level editor.
    """

    def __init__(self, level_view: LevelView, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.level_view = level_view
        self.level_ref = level_view.level_ref

        with open(jump_creator_flags_path, "r") as data:
            flags = loads(data.read())
        setup_layout(self, flags)

    @undoable
    def add_jump(self):
        self.level_view.add_jump()

    def show_jump_dest(self):
        header_editor = HeaderEditor(self, self.level_ref)
        header_editor.tab_widget.setCurrentIndex(3)
        header_editor.exec_()
