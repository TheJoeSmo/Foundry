from PySide6.QtWidgets import QGridLayout, QGroupBox, QVBoxLayout

from foundry.core.palette import (
    PALETTE_GROUPS_PER_OBJECT_SET,
    PALETTES_PER_PALETTES_GROUP,
)
from foundry.core.palette.PaletteGroup import MutablePaletteGroup
from foundry.game.level.LevelRef import LevelRef
from foundry.gui.CustomDialog import CustomDialog
from foundry.gui.PaletteWidget import PaletteWidget


class PaletteViewer(CustomDialog):
    palettes_per_row = 4

    def __init__(self, parent, level_ref: LevelRef):
        title = f"MutablePalette Groups for Object Set {level_ref.level.object_set_number}"

        super().__init__(parent, title=title)

        self.level_ref = level_ref

        layout = QGridLayout(self)

        for palette_group in range(PALETTE_GROUPS_PER_OBJECT_SET):
            group_box = QGroupBox()
            group_box.setTitle(f"MutablePalette Group {palette_group}")

            group_box_layout = QVBoxLayout(group_box)
            group_box_layout.setSpacing(0)

            pal = MutablePaletteGroup.from_tileset(self.level_ref.level.object_set_number, palette_group)

            for idx in range(PALETTES_PER_PALETTES_GROUP):
                group_box_layout.addWidget(PaletteWidget(self, pal[idx]))

            row = palette_group // self.palettes_per_row
            col = palette_group % self.palettes_per_row

            layout.addWidget(group_box, row, col)
