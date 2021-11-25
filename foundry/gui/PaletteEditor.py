from typing import Optional

from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtWidgets import QHBoxLayout, QWidget

from foundry.game.gfx.Palette import PALETTE_GROUPS_PER_OBJECT_SET, PaletteGroup
from foundry.game.level.Level import Level
from foundry.gui.PaletteGroupEditor import PaletteGroupEditor


class PaletteEditor(QWidget):
    palette_updated: SignalInstance = Signal(PaletteGroup, PaletteGroup)  # type: ignore

    def __init__(
        self,
        parent: Optional[QWidget],
        bg_palette_group: Optional[PaletteGroup] = None,
        spr_palette_group: Optional[PaletteGroup] = None,
    ):
        super().__init__(parent=parent)
        self._bg_palette_group = (
            bg_palette_group
            if bg_palette_group is not None
            else PaletteGroup(0, 0, [bytearray([0] * 4) for i in range(4)])
        )
        self._spr_palette_group = (
            spr_palette_group
            if spr_palette_group is not None
            else PaletteGroup(0, 0, [bytearray([0] * 4) for i in range(4)])
        )

        layout = QHBoxLayout()
        layout.setSpacing(0)
        self.background_palette_widget = PaletteGroupEditor(self, self.bg_palette_group)
        self.background_palette_widget.palette_updated.connect(lambda *_: self.on_palette_update())
        layout.addWidget(self.background_palette_widget)
        self.sprite_palette_widget = PaletteGroupEditor(self, self.spr_palette_group)
        self.sprite_palette_widget.palette_updated.connect(lambda *_: self.on_palette_update())
        layout.addWidget(self.sprite_palette_widget)
        self.setLayout(layout)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.parent}, {self.bg_palette_group}, {self.spr_palette_group})"

    def load_from_level(self, level: Level):
        self.background_palette_widget.load(level.object_set_number, level.object_palette_index)
        self._bg_palette_group = self.background_palette_widget.palette_group
        self.sprite_palette_widget.load(
            level.object_set_number, level.enemy_palette_index + PALETTE_GROUPS_PER_OBJECT_SET
        )
        self._spr_palette_group = self.sprite_palette_widget.palette_group

    @property
    def changed(self) -> bool:
        return self.bg_palette_group.changed or self.spr_palette_group.changed

    @changed.setter
    def changed(self, value: bool):
        self.bg_palette_group.changed = value
        self.spr_palette_group.changed = value

    @property
    def bg_palette_group(self) -> PaletteGroup:
        return self._bg_palette_group

    @bg_palette_group.setter
    def bg_palette_group(self, palette: PaletteGroup):
        self._bg_palette_group = palette
        self.background_palette_widget.palette_group = palette

    @property
    def spr_palette_group(self) -> PaletteGroup:
        return self._spr_palette_group

    @spr_palette_group.setter
    def spr_palette_group(self, palette: PaletteGroup):
        self._spr_palette_group = palette
        self.sprite_palette_widget.palette_group = palette

    def on_palette_update(self):
        self.palette_updated.emit(self.bg_palette_group, self.spr_palette_group)
        self.changed
