from typing import Optional

from PySide6.QtCore import QSize, Signal, SignalInstance
from PySide6.QtGui import Qt
from PySide6.QtWidgets import (
    QAbstractButton,
    QDialogButtonBox,
    QGridLayout,
    QVBoxLayout,
    QWidget,
)

from foundry.game.gfx.Palette import NESPalette
from foundry.gui.ColorButtonWidget import ColorButtonWidget
from foundry.gui.CustomDialog import CustomDialog


class ColorSelector(CustomDialog):
    ROWS = 4
    COLUMNS = 16

    ok_clicked: SignalInstance = Signal(int)  # type: ignore

    def __init__(self, parent: Optional[QWidget], title: str = "NES Color Table", size: Optional[QSize] = None):
        super().__init__(parent, title=title)

        self.size_ = size if not None else QSize(24, 24)

        self._selected_button = 0

        self.layout_ = QGridLayout()
        self.layout_.setSpacing(0)

        self._color_buttons = []
        for row in range(self.ROWS):
            for column in range(self.COLUMNS):
                color = NESPalette[row * self.COLUMNS + column]
                button = ColorButtonWidget(self, color, self.size_)
                button.setLineWidth(0)
                self._color_buttons.append(button)
                self.layout_.addWidget(button, row, column)
        self._color_buttons[0].selected = True

        for idx, btn in enumerate(self._color_buttons):
            btn.clicked.connect(lambda idx=idx: self._on_click(idx))

        self.buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttons.clicked.connect(self._on_button)  # type: ignore

        layout = QVBoxLayout(self)
        layout.addLayout(self.layout_)

        layout.addWidget(self.buttons, alignment=Qt.AlignCenter)

    @property
    def last_selected_color_index(self) -> int:
        return self._selected_button

    def _on_click(self, index: int):
        self._color_buttons[self._selected_button].selected = False
        self._color_buttons[index].selected = True
        self._selected_button = index

    def _on_button(self, button: QAbstractButton):
        if button is self.buttons.button(QDialogButtonBox.Ok):  # ok button
            self.accept()
        else:
            self.reject()
