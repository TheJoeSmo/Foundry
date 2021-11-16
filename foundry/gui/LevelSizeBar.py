from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QFormLayout, QLabel, QSizePolicy, QWidget

from foundry.gui.util import ease_color


class SizeBar(QWidget):
    def __init__(self, parent: QWidget, current_value: int, maximum_value: int):
        super(SizeBar, self).__init__(parent)

        self._maximum_value = maximum_value
        self._current_value = current_value
        self.value_color = QColor.black

    def sizeHint(self) -> QSize:
        size = super(SizeBar, self).sizeHint()
        size.setHeight(10)
        return size

    @property
    def current_value(self) -> int:
        return self._current_value

    @current_value.setter
    def current_value(self, value: int):
        self._current_value = value
        self.update()

    @property
    def maximum_value(self) -> int:
        return self._maximum_value

    @maximum_value.setter
    def maximum_value(self, value: int):
        self._maximum_value = value
        self.update()

    @property
    def display_color(self) -> QColor:
        if self.maximum_value == 0:
            return QColor(136, 8, 8)
        if self.current_value > self.maximum_value:
            overload = min((self.current_value - self.maximum_value) / 100, 1)
            return ease_color(QColor(136, 8, 8), QColor(255, 255, 0), overload)
        if 0.9 <= self.current_value / self.maximum_value <= 1:
            overload = ((self.current_value / self.maximum_value) - 0.9) * 10
            return ease_color(QColor(255, 255, 0), QColor(34, 139, 34), overload)
        else:
            return QColor(34, 139, 34)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.fillRect(event.rect(), self.palette().base())

        total_length = max(self.current_value, self.maximum_value, 1)

        pixels_per_byte = event.rect().width() / total_length

        bar = QRect(event.rect())
        bar.setWidth(int(pixels_per_byte * self.current_value))

        painter.fillRect(bar, self.display_color)


class LevelSizeBar(QWidget):
    def __init__(self, parent, label: str, current_value: int, maximum_value: int):
        super(LevelSizeBar, self).__init__(parent)

        self.label = label
        self._current_value = current_value

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.setWhatsThis(
            "<b>Size Bar</b><br/>"
            "This bar shows, how much of the available space inside the level is currently taken up. It will turn "
            "red, when too many level objects have been placed (or if the level objects would result in more bytes, "
            "than the level originally had)."
        )

        self.bar = SizeBar(self, current_value, maximum_value)

        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)

        layout = QFormLayout(self)
        layout.addRow(self.info_label, self.bar)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

    def update(self):
        self.info_label.setText(f"{self.label}: {self.current_value}/{self.maximum_value} Bytes")
        return super(LevelSizeBar, self).update()

    @property
    def current_value(self) -> int:
        return self.bar.current_value

    @current_value.setter
    def current_value(self, value: int):
        self.bar.current_value = value
        self.update()

    @property
    def maximum_value(self) -> int:
        return self.bar.maximum_value

    @maximum_value.setter
    def maximum_value(self, value: int):
        self.bar.maximum_value = value
        self.update()
