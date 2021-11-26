from typing import Union

from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtWidgets import QScrollArea, QTabWidget

from foundry.game.gfx.objects.EnemyItem import EnemyObject
from foundry.game.gfx.objects.LevelObject import LevelObject
from foundry.gui.ObjectIcon import ObjectButton
from foundry.gui.ObjectToolBox import ObjectToolBox


class TabbedToolBox(QTabWidget):
    selected: SignalInstance = Signal(ObjectButton)  # type: ignore
    selected_index: SignalInstance = Signal(int, int)  # type: ignore
    object_placed: SignalInstance = Signal(ObjectButton)  # type: ignore

    def __init__(self, parent=None):
        super(TabbedToolBox, self).__init__(parent)

        self.setTabPosition(self.East)

        self._recent_toolbox = ObjectToolBox(self)
        self._recent_toolbox.object_icon_clicked.connect(self.selected)
        self._recent_toolbox.object_selected.connect(lambda index: self.selected_index.emit(0, index))
        self._recent_toolbox.object_placed.connect(self._on_object_dragged)

        self._objects_toolbox = ObjectToolBox(self)
        self._objects_toolbox.object_icon_clicked.connect(self.selected)
        self._objects_toolbox.object_selected.connect(lambda index: self.selected_index.emit(1, index))
        self._objects_toolbox.object_placed.connect(self._on_object_dragged)

        self._enemies_toolbox = ObjectToolBox(self)
        self._enemies_toolbox.object_icon_clicked.connect(self.selected)
        self._enemies_toolbox.object_selected.connect(lambda index: self.selected_index.emit(2, index))
        self._enemies_toolbox.object_placed.connect(self._on_object_dragged)

        self._recent_scroll_area = QScrollArea(self)
        self._recent_scroll_area.setWidgetResizable(True)
        self._recent_scroll_area.setWidget(self._recent_toolbox)

        self._object_scroll_area = QScrollArea(self)
        self._object_scroll_area.setWidgetResizable(True)
        self._object_scroll_area.setWidget(self._objects_toolbox)

        self._enemies_scroll_area = QScrollArea(self)
        self._enemies_scroll_area.setWidgetResizable(True)
        self._enemies_scroll_area.setWidget(self._enemies_toolbox)

        self.addTab(self._recent_scroll_area, "Recent")
        self.addTab(self._object_scroll_area, "Objects")
        self.addTab(self._enemies_scroll_area, "Enemies")

        self.show_level_object_tab()

        self.setWhatsThis(
            "<b>Object Toolbox</b><br/>"
            "Contains all objects and enemies/items, that can be placed in this type of level. Which are "
            "available depends on the object set, that is selected for this level.<br/>"
            "You can drag and drop objects into the level or click to select them. After selecting "
            "an object, you can place it by clicking the middle mouse button anywhere in the level."
            "<br/><br/>"
            "Note: Some items, like blocks with items in them, are displayed as they appear in the ROM, "
            "mouse over them and check their names in the ToolTip, or use the object dropdown to find "
            "them directly."
        )

    def sizeHint(self):
        size = super().sizeHint()
        width = self._recent_toolbox.sizeHint().width()
        width = max(width, self._objects_toolbox.sizeHint().width())
        width = max(width, self._enemies_toolbox.sizeHint().width())

        size.setWidth(
            max(width, size.width()) + self.tabBar().width() + self._object_scroll_area.verticalScrollBar().width() + 10
        )

        return size

    def show_recent_tab(self):
        self.setCurrentIndex(self.indexOf(self._recent_toolbox))

    def show_level_object_tab(self):
        self.setCurrentIndex(self.indexOf(self._object_scroll_area))

    def show_enemy_item_tab(self):
        self.setCurrentIndex(self.indexOf(self._enemies_scroll_area))

    def select_object(self, tab_index: int, object_index: int) -> Union[LevelObject, EnemyObject]:
        if tab_index == 0:
            return self._recent_toolbox.objects[object_index]
        elif tab_index == 1:
            return self._objects_toolbox.objects[object_index]
        else:
            return self._enemies_toolbox.objects[object_index]

    def set_object_set(self, object_set_index, graphic_set_index=-1):
        self._recent_toolbox.clear()
        self._objects_toolbox.clear()
        self._objects_toolbox.add_from_object_set(object_set_index, graphic_set_index)

        self._enemies_toolbox.clear()
        self._enemies_toolbox.add_from_enemy_set(object_set_index)

    def add_recent_object(self, level_object: Union[EnemyObject, LevelObject]):
        self._recent_toolbox.place_at_front(level_object)

    def _on_object_dragged(self, object_icon: ObjectButton):
        self.add_recent_object(object_icon.item)
