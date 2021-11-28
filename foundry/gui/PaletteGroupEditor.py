from typing import Callable, Optional

from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtWidgets import QVBoxLayout, QWidget

from foundry.game.gfx.Palette import (
    COLORS_PER_PALETTE,
    PALETTES_PER_PALETTES_GROUP,
    PaletteGroup,
    load_palette_group,
)
from foundry.gui.PaletteViewer import PaletteWidget


class PaletteGroupEditor(QWidget):
    palette_updated: SignalInstance = Signal(PaletteGroup)  # type: ignore

    def __init__(self, parent: Optional[QWidget], palette_group: PaletteGroup):
        super().__init__(parent=parent)
        self._palette_group = palette_group

        layout = QVBoxLayout()
        layout.setSpacing(0)
        self.palettes = []
        for short_palette_index in range(PALETTES_PER_PALETTES_GROUP):
            widget = PaletteWidget(self, palette_group, short_palette_index)
            widget.color_changed.connect(self.on_color_update(short_palette_index))
            widget.clickable = True
            self.palettes.append(widget)
            layout.addWidget(widget)

        self.setLayout(layout)

    def load(self, object_set: int, palette_group_index: int):
        self._palette_group = load_palette_group(object_set, palette_group_index)
        for palette in self.palettes:
            palette._palette_group = self._palette_group
            palette._update_colors()

    @property
    def palette_group(self) -> PaletteGroup:
        return self._palette_group

    @palette_group.setter
    def palette_group(self, palette_group: PaletteGroup):
        self._palette_group = palette_group
        for idx in range(PALETTES_PER_PALETTES_GROUP):
            for color in range(COLORS_PER_PALETTE):
                self.palette_group[idx][color] = palette_group[idx][color]

        self.palette_group.changed = True

    def on_color_update(self, short_palette_index: int) -> Callable[[int, int], None]:
        def color_update(index: int, color_index: int):
            if self.palette_group[short_palette_index][index] == color_index:
                return

            # colors at index 0 are shared among all palettes of a palette group
            if index == 0:
                for idx, palette in enumerate(self.palette_group):  # type: ignore
                    palette[0] = color_index
                    self.palettes[idx]._update_colors()
            else:
                self.palette_group[short_palette_index][index] = color_index

            self.palette_group.changed = True
            self.palette_updated.emit(self.palette_group)

        return color_update
