from itertools import product
from typing import Optional, Union

from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtWidgets import QWidget

from foundry.game.gfx.objects.EnemyItem import EnemyObject
from foundry.game.gfx.objects.EnemyItemFactory import EnemyItemFactory
from foundry.game.gfx.objects.LevelObject import LevelObject
from foundry.game.gfx.objects.LevelObjectFactory import LevelObjectFactory
from foundry.gui.FlowLayout import FlowLayout
from foundry.gui.ObjectIcon import ObjectButton
from foundry.gui.util import clear_layout
from foundry.smb3parse.objects import MAX_DOMAIN, MAX_ENEMY_ITEM_ID, MAX_ID_VALUE


class ObjectToolBox(QWidget):
    object_icon_clicked: SignalInstance = Signal(ObjectButton)  # type: ignore
    object_placed: SignalInstance = Signal(ObjectButton)  # type: ignore
    object_selected: SignalInstance = Signal(int)  # type: ignore

    def __init__(self, parent: Optional[QWidget] = None):
        super(ObjectToolBox, self).__init__(parent)
        self._layout = FlowLayout(self)
        self.objects: list[Union[EnemyObject, LevelObject]] = []

    def update(self):
        self._layout.clear()
        for idx, object in enumerate(self.objects):
            icon = ObjectButton(self, object)
            icon.selected.connect(self._on_icon_clicked)
            icon.selected.connect(lambda idx=idx: self.object_selected.emit(idx))
            icon.object_created.connect(lambda icon=icon: self.object_placed.emit(icon))
            self._layout.addWidget(icon)

    def add_object(self, level_object: Union[EnemyObject, LevelObject]):
        self.objects.append(level_object)
        self.update()

    def add_from_object_set(self, object_set_index: int, graphic_set_index: int = -1):
        if graphic_set_index == -1:
            graphic_set_index = object_set_index

        factory = LevelObjectFactory(
            object_set_index, graphic_set_index, 0, [], vertical_level=False, size_minimal=True
        )

        object_ids = list(range(0x00, 0x10)) + list(range(0x10, MAX_ID_VALUE, 0x10))

        for domain, obj_index in product(range(MAX_DOMAIN + 1), object_ids):
            level_object = factory.from_properties(
                domain=domain, object_index=obj_index, x=0, y=0, length=None, index=0
            )

            if not isinstance(level_object, LevelObject) or level_object.name in ["MSG_NOTHING", "MSG_CRASH"]:
                continue

            self.objects.append(level_object)
        self.update()

    def add_from_enemy_set(self, object_set_index: int):
        self.clear()
        factory = EnemyItemFactory(object_set_index, 0)

        for obj_index in range(MAX_ENEMY_ITEM_ID + 1):
            enemy_item = factory.from_properties(obj_index, x=0, y=0)

            if enemy_item.name in ["MSG_NOTHING", "MSG_CRASH"]:
                continue

            self.objects.append(enemy_item)
        self.update()

    def clear(self):
        clear_layout(self._layout)
        self._layout.clear()
        self.objects = []

    def _on_icon_clicked(self):
        self.object_icon_clicked.emit(self.sender())

    @property
    def draw_background_color(self):
        return self.objects[0].draw_background_color

    @draw_background_color.setter
    def draw_background_color(self, value):
        for index in range(self._layout.count()):
            self.objects[index].draw_background_color = value

    def place_at_front(self, object: Union[LevelObject, EnemyObject]):
        for idx, obj in enumerate(self.objects):
            if obj.name == object.name:
                self.objects.pop(idx)
                break
        self.objects.insert(0, object)
        clear_layout(self._layout)
        self.update()
