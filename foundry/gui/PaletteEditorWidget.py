from PySide6.QtWidgets import QDialog, QWidget

from foundry.core.palette.Palette import MutablePaletteProtocol
from foundry.gui.ColorSelector import ColorSelector
from foundry.gui.PaletteWidget import PaletteWidget


class PaletteEditorWidget(PaletteWidget):
    def __init__(self, parent: QWidget | None, palette: MutablePaletteProtocol):
        super().__init__(parent, palette)

        for idx, btn in enumerate(self._buttons):
            btn.clicked.connect(lambda idx=idx: self._open_color_selector(idx))

    def _open_color_selector(self, button_index: int):
        selector = ColorSelector(self)

        if QDialog.Accepted == selector.exec_():
            palette = self.palette
            palette[button_index] = selector.last_selected_color_index
            self.palette = palette
