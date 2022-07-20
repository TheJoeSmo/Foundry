from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtWidgets import QVBoxLayout, QWidget

from foundry.core.palette.PaletteGroup import PaletteGroup
from foundry.gui.PaletteEditorWidget import PaletteEditorWidget


class PaletteGroupEditor(QWidget):
    palette_group_changed: SignalInstance = Signal(PaletteGroup)  # type: ignore

    def __init__(self, parent: QWidget | None, palette_group: PaletteGroup):
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
    def palette_group(self) -> PaletteGroup:
        return self._palette_group

    @palette_group.setter
    def palette_group(self, palette_group: PaletteGroup):
        self._palette_group = palette_group
        self.palette_group_changed.emit(palette_group)
        self._palette_group = palette_group  # Force the value
        self._update()

    def _update(self):
        palette_group = self._palette_group
        for idx, palette in enumerate(self._palettes):
            palette._palette = palette_group[idx]
            palette._update()
        self._palette_group = palette_group

    def _on_palette_changed(self, palette_index: int):
        self.palette_group = self.palette_group.evolve_palettes(palette_index, self._palettes[palette_index].palette)
