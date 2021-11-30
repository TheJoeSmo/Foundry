from typing import Optional

from PySide6.QtCore import QObject, Signal, SignalInstance

from foundry.core.UndoController import UndoController
from foundry.game.level import LevelByteData
from foundry.game.level.Level import Level


class LevelRef(QObject):
    data_changed: SignalInstance = Signal()  # type: ignore
    jumps_changed: SignalInstance = Signal()  # type: ignore

    def __init__(self):
        super(LevelRef, self).__init__()
        self._internal_level = None
        self._undo_controller = None
        self._is_loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def load_level(self, level_name: str, object_data_offset: int, enemy_data_offset: int, object_set_number: int):
        self.level = Level(level_name, object_data_offset, enemy_data_offset, object_set_number)
        self._is_loaded = True

        # actively emit, because we weren't connected yet, when the level sent it out
        self.data_changed.emit()

    def unload_level(self) -> None:
        self._internal_level = None
        self._undo_controller = None
        self._is_loaded = False

    @property
    def level(self) -> Level:
        assert self._internal_level is not None

        return self._internal_level

    @level.setter
    def level(self, level: Level):
        self._internal_level = level

        self._undo_controller = UndoController(self._internal_level.to_bytes())

        self._internal_level.data_changed.connect(self.data_changed.emit)
        self._internal_level.jumps_changed.connect(self.jumps_changed.emit)

    @property
    def selected_objects(self):
        assert self._internal_level is not None

        return [obj for obj in self._internal_level.get_all_objects() if obj.selected]

    @selected_objects.setter
    def selected_objects(self, selected_objects):
        assert self._internal_level is not None

        if selected_objects == self.selected_objects:
            return

        for obj in self._internal_level.get_all_objects():
            obj.selected = obj in selected_objects

        self.data_changed.emit()

    @property
    def state(self) -> LevelByteData:
        assert self._undo_controller is not None

        return self._undo_controller.state

    def do(self, level_data: Optional[LevelByteData] = None) -> LevelByteData:
        assert self._undo_controller is not None

        data = self._undo_controller.do(level_data if level_data is not None else self.level.to_bytes())
        self.data_changed.emit()
        return data

    @property
    def can_undo(self) -> bool:
        assert self._undo_controller is not None

        return self._undo_controller.can_undo

    def undo(self) -> LevelByteData:
        assert self._undo_controller is not None

        new_state = self._undo_controller.undo()
        self.set_level_state(*new_state)
        return new_state

    @property
    def can_redo(self) -> bool:
        assert self._undo_controller is not None

        return self._undo_controller.can_redo

    def redo(self) -> LevelByteData:
        assert self._undo_controller is not None

        new_state = self._undo_controller.redo()
        self.set_level_state(*new_state)
        return new_state

    def set_level_state(self, object_data, enemy_data):
        self.level.from_bytes(object_data, enemy_data, new_level=False)
        self.level.changed = True

        self.data_changed.emit()

    def save_level_state(self):
        assert self._internal_level is not None
        assert self._undo_controller is not None

        self.do(self._internal_level.to_bytes())
        self.level.changed = True

        self.data_changed.emit()

    def __bool__(self):
        return self.is_loaded
