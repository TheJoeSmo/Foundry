from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtWidgets import QVBoxLayout, QWidget

from foundry.core.palette.PaletteGroup import MutablePaletteGroupProtocol
from foundry.gui.PaletteEditorWidget import PaletteEditorWidget


class PaletteGroupEditor(QWidget):
    palette_group_changed: SignalInstance = Signal(MutablePaletteGroupProtocol)  # type: ignore

    def __init__(self, parent: QWidget | None, palette_group: MutablePaletteGroupProtocol):
        super().__init__(parent)
        self._palette_group = palette_group

        layout = QVBoxLayout()
        layout.setSpacing(0)

        self._palettes: list[PaletteEditorWidget] = []
        for idx, palette in enumerate(palette_group.palettes):
            widget = PaletteEditorWidget(self, palette)
            widget.palette_changed.connect(lambda *_, idx=idx: self._on_palette_changed(idx))
            self._palettes.append(widget)
            layout.addWidget(widget)

        self.setLayout(layout)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.parent}, {self.palette_group})"

    @property
    def palette_group(self) -> MutablePaletteGroupProtocol:
        return self._palette_group

    @palette_group.setter
    def palette_group(self, palette_group: MutablePaletteGroupProtocol):
        self._palette_group = palette_group
        self.palette_group_changed.emit(palette_group)
        self._update()

    def _update(self):
        for idx, palette in enumerate(self._palettes):
            palette._palette = self._palette_group[idx]
            palette._update()

    def _on_palette_changed(self, palette_index: int):
        palette_group = self.palette_group
        palette_group.palettes[palette_index] = self._palettes[palette_index].palette
        for palette in palette_group:
            palette[0] = palette_group[palette_index][0]
        self.palette_group = palette_group
