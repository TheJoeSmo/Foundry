from PySide6.QtCore import QEvent, QRect, Qt, Signal, SignalInstance
from PySide6.QtGui import QCursor, QFocusEvent
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from foundry.game.gfx.objects.LevelObject import LevelObject
from foundry.game.level.LevelRef import LevelRef
from foundry.gui.LevelView import LevelView
from foundry.gui.ObjectList import ObjectList
from foundry.gui.util import clear_layout


class WarningList(QWidget):
    warnings_updated: SignalInstance = Signal(bool)

    def __init__(self, parent, level_ref: LevelRef, level_view_ref: LevelView, object_list_ref: ObjectList):
        super().__init__(parent)

        self.level_ref = level_ref
        self.level_ref.data_changed.connect(self._update_warnings)

        self.level_view_ref = level_view_ref
        self.object_list = object_list_ref

        self.setLayout(QVBoxLayout())
        self.setWindowFlag(Qt.Popup)
        self.layout().setContentsMargins(5, 5, 5, 5)

        self._enemy_dict = {}

        self.warnings: list[tuple[str, list[LevelObject]]] = []

    def _update_warnings(self):
        self.warnings.clear()

        level = self.level_ref.level

        for index, obj in enumerate(level.objects + level.enemies + level.jumps):
            for warning in obj.definition.get_warnings():
                if warning.check_object(obj, level=level, index=index):
                    self.warnings.append((warning.get_message(obj), [obj]))

        self.update()
        self.warnings_updated.emit(bool(self.warnings))

    def update(self):
        self.hide()

        clear_layout(self.layout())

        for warning in self.warnings:
            warning_message, related_objects = warning

            label = WarningLabel(warning_message, related_objects)
            label.hovered.connect(self._focus_objects)

            self.layout().addWidget(label)

        super().update()

    def show(self):
        pos = QCursor.pos()
        pos.setY(pos.y() + 10)

        self.setGeometry(QRect(pos, self.layout().sizeHint()))

        super().show()

    def _focus_objects(self):
        objects = self.sender().related_objects

        if objects:
            self.level_ref.blockSignals(True)

            self.level_view_ref.select_objects(objects)
            self.level_view_ref.scroll_to_objects(objects)
            self.object_list.update_content()

            self.level_ref.blockSignals(False)

    def focusOutEvent(self, event: QFocusEvent):
        self.hide()

        super().focusOutEvent(event)


class WarningLabel(QLabel):
    hovered: SignalInstance = Signal()

    def __init__(self, text: str, related_objects: list[LevelObject]):
        super().__init__(text)

        self.related_objects = related_objects

    def enterEvent(self, event: QEvent):
        self.hovered.emit()

        return super().enterEvent(event)
