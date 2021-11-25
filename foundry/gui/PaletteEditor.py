from typing import Callable

from PySide6.QtWidgets import QVBoxLayout, QWidget

from foundry.game.gfx.Palette import (
    PALETTES_PER_PALETTES_GROUP,
    PaletteGroup,
    load_palette_group,
)
from foundry.game.level.LevelRef import LevelRef
from foundry.gui.PaletteViewer import PaletteWidget
from foundry.gui.util import clear_layout


class PaletteEditor(QWidget):
    def __init__(self, level_ref: LevelRef):
        super(PaletteEditor, self).__init__()

        self.level_ref = level_ref

        self.level_ref.data_changed.connect(self.update)

        self.setLayout(QVBoxLayout(self))
        self.layout().setSpacing(0)

        self.setWhatsThis(
            "<b>Object Palettes</b><br/>"
            "This shows the current palette group of the level, which can be changed in the level header "
            "editor.<br/>"
            "By clicking on the individual colors, you can change them.<br/><br/>"
            ""
            "Note: The first color (the left most one) is always the same among all 4 palettes."
        )

    def update(self):
        clear_layout(self.layout())

        palette_group_index = self.level_ref.level.object_palette_index
        palette_group = load_palette_group(self.level_ref.level.object_set_number, palette_group_index)

        for palette_no in range(PALETTES_PER_PALETTES_GROUP):
            widget = PaletteWidget(palette_group, palette_no)
            widget.color_changed.connect(self.color_changer(palette_group, palette_no))
            widget.clickable = True

            self.layout().addWidget(widget)

    def color_changer(self, palette_group: PaletteGroup, palette_no: int) -> Callable:
        def actual_changer(index_in_palette, index_in_nes_color_table):
            if palette_group[palette_no][index_in_palette] == index_in_nes_color_table:
                return

            # colors at index 0 are shared among all palettes of a palette group
            if index_in_palette == 0:
                for palette in palette_group.palettes:
                    palette[0] = index_in_nes_color_table
            else:
                palette_group[palette_no][index_in_palette] = index_in_nes_color_table

            PaletteGroup.changed = True

            self.level_ref.level.reload()

        return actual_changer
