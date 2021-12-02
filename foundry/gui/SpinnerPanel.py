from json import loads
from typing import Optional

from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtWidgets import QSizePolicy, QWidget

from foundry import spinner_panel_flags_path
from foundry.game.gfx.objects.LevelObject import LevelObject
from foundry.game.gfx.objects.ObjectLike import ObjectLike
from foundry.game.level.LevelRef import LevelRef
from foundry.gui.util import setup_description, setup_layout

MAX_DOMAIN = 0x07
MAX_TYPE = 0xFF
MAX_LENGTH = 0xFF


class SpinnerPanel(QWidget):
    object_change: SignalInstance = Signal(int)

    zoom_in_triggered: SignalInstance = Signal()
    zoom_out_triggered: SignalInstance = Signal()

    def __init__(self, parent: Optional[QWidget], level_ref: LevelRef):
        super(SpinnerPanel, self).__init__(parent)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.level_ref = level_ref
        self.level_ref.data_changed.connect(self.update)

        with open(spinner_panel_flags_path, "r") as data:
            flags = loads(data.read())
        setup_layout(self, flags)
        setup_description(self, flags)

    def update(self):
        if len(self.level_ref.selected_objects) == 1:
            selected_object = self.level_ref.selected_objects[0]

            if isinstance(selected_object, ObjectLike):
                self._populate_spinners(selected_object)

        else:
            self.disable_all()

        super(SpinnerPanel, self).update()

    def _populate_spinners(self, obj: ObjectLike):
        self.blockSignals(True)

        self.set_type(obj.obj_index)

        if isinstance(obj, LevelObject):
            self.enable_domain(True, obj.domain)
        else:
            self.enable_domain(False)

        if isinstance(obj, LevelObject) and obj.is_4byte:
            self.set_length(obj.length)
        else:
            self.enable_length(False)

        self.blockSignals(False)

    def get_type(self):
        return self.spin_type.value()

    def set_type(self, object_type: int):
        self.spin_type.setValue(object_type)
        self.spin_type.setEnabled(True)

    def get_domain(self):
        return self.spin_domain.value()

    def set_domain(self, domain: int):
        self.spin_domain.setValue(domain)
        self.spin_domain.setEnabled(True)

    def get_length(self) -> int:
        return self.spin_length.value()

    def set_length(self, length: int):
        self.spin_length.setValue(length)
        self.spin_length.setEnabled(True)

    def enable_type(self, enable: bool, value: int = 0):
        self.spin_type.setValue(value)
        self.spin_type.setEnabled(enable)

    def enable_domain(self, enable: bool, value: int = 0):
        self.spin_domain.setValue(value)
        self.spin_domain.setEnabled(enable)

    def enable_length(self, enable: bool, value: int = 0):
        self.spin_length.setValue(value)
        self.spin_length.setEnabled(enable)

    def clear_spinners(self):
        self.set_type(0x00)
        self.set_domain(0x00)
        self.set_length(0x00)

    def disable_all(self):
        self.blockSignals(True)

        self.clear_spinners()

        self.enable_type(False)
        self.enable_domain(False)
        self.enable_length(False)

        self.blockSignals(False)
