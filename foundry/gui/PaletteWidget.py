from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtWidgets import QHBoxLayout, QWidget

from foundry.core.palette import Palette
from foundry.gui.ColorButtonWidget import ColorButtonWidget


class PaletteWidget(QWidget):
    """
    A widget to view the palette.

    Attributes
    ----------
    palette_changed: Signal[palette]
        Slot associated with the palette viewer changing its palette.
    """

    palette_changed: SignalInstance = Signal(Palette)  # type: ignore

    def __init__(self, parent: QWidget | None, palette: Palette):
        super().__init__(parent)
        self._palette = palette

        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 2, 0, 2)

        self._buttons = [ColorButtonWidget(self, color.to_qt()) for color in palette]

        for button in self._buttons:
            layout.addWidget(button)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.parent}, {self.palette})"

    @property
    def palette(self) -> Palette:
        return self._palette

    @palette.setter
    def palette(self, palette: Palette):
        self._palette = palette
        self.palette_changed.emit(palette)
        self._update()

    def _update(self):
        for idx, color in enumerate(self.palette):
            self._buttons[idx].color = color.to_qt()
