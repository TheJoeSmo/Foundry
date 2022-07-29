from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtWidgets import QHBoxLayout, QWidget

from foundry.core.palette.Palette import MutablePaletteProtocol
from foundry.gui.ColorButtonWidget import ColorButtonWidget


class PaletteWidget(QWidget):
    """
    A widget to view the palette.

    Attributes
    ----------
    palette_changed: Signal[palette]
        Slot associated with the palette viewer changing its palette.
    """

    palette_changed: SignalInstance = Signal(MutablePaletteProtocol)  # type: ignore

    def __init__(self, parent: QWidget | None, palette: MutablePaletteProtocol):
        super().__init__(parent)
        self._palette = palette

        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 2, 0, 2)

        self._buttons = [ColorButtonWidget(self, color) for color in palette.colors]

        for button in self._buttons:
            layout.addWidget(button)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.parent}, {self.palette})"

    @property
    def palette(self) -> MutablePaletteProtocol:
        return self._palette

    @palette.setter
    def palette(self, palette: MutablePaletteProtocol):
        self._palette = palette
        self.palette_changed.emit(palette)
        self._update()

    def _update(self):
        for idx, color in enumerate(self.palette.colors):
            self._buttons[idx].color = color
