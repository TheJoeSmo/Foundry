from PySide6.QtCore import QSize, Signal, SignalInstance
from PySide6.QtGui import QColor, QMouseEvent, QPixmap, Qt
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget


class ColorButtonWidget(QLabel):
    """
    A colored button that can be pressed and interacted with

    Attributes
    ----------
    clicked: Signal
        Slot associated with the button being clicked.
    size_changed: Signal[QSize]
        Slot associated with the button changing size.
    color_changed: Signal[QColor]
        Slot associated with the button changing color.
    selected_changed: Signal[bool]
        Slot associated with the button changing its selected state.
    """

    clicked: SignalInstance = Signal()  # type: ignore
    size_changed: SignalInstance = Signal(QSize)  # type: ignore
    color_changed: SignalInstance = Signal(QColor)  # type: ignore
    selected_changed: SignalInstance = Signal(bool)  # type: ignore

    def __init__(
        self,
        parent: QWidget | None,
        color: QColor | None = None,
        size: QSize | None = None,
        selected: bool = False,
    ):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        if color is not None:
            self._color = color
        else:
            self._color = QColor(Qt.white)
        if size is not None:
            self._size_ = size
        else:
            self._size_ = QSize(16, 16)
        self._selected = selected
        self._update()

    @property
    def size_(self) -> QSize:
        return self._size_

    @size_.setter
    def size_(self, size: QSize):
        self._size_ = size
        self.size_changed.emit(size)
        self._update()

    @property
    def color(self) -> QColor:
        return self._color

    @color.setter
    def color(self, color: QColor):
        self._color = color
        self.color_changed.emit(color)
        self._update()

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, selected: bool):
        self._selected = selected
        self.selected_changed.emit(selected)
        self._update()

    def _update(self):
        pix = QPixmap(self.size_)
        pix.fill(self.color)
        self.setPixmap(pix)

        if self.selected:
            if self.color.lightnessF() < 0.25:
                self.setStyleSheet("border-color: rgb(255, 255, 255); border-width: 2px; border-style: solid")
            else:
                self.setStyleSheet("border-color: rgb(0, 0, 0); border-width: 2px; border-style: solid")
        else:
            rgb = self.color.getRgb()
            self.setStyleSheet(
                f"border-color: rgb({rgb[0]}, {rgb[1]}, {rgb[2]}); border-width: 2px; border-style: solid"
            )

        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.clicked.emit()
