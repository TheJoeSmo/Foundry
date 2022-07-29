from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtWidgets import QHBoxLayout, QWidget

from foundry.core.palette.PaletteGroup import MutablePaletteGroup
from foundry.game.File import ROM
from foundry.game.level.Level import Level
from foundry.gui.PaletteGroupEditor import PaletteGroupEditor
from foundry.gui.PaletteGroupModel import PaletteGroupModel


class PaletteGroupController(QWidget):
    palette_group_changed: SignalInstance = Signal(MutablePaletteGroup, MutablePaletteGroup)  # type: ignore

    def __init__(
        self,
        parent: QWidget | None,
        tileset: int = 0,
        bg_offset: int = 0,
        spr_offset: int = 0,
        bg_palette_group: MutablePaletteGroup | None = None,
        spr_palette_group: MutablePaletteGroup | None = None,
    ):
        super().__init__(parent)

        self.model = PaletteGroupModel(
            tileset,
            bg_offset,
            spr_offset,
            bg_palette_group if bg_palette_group is not None else MutablePaletteGroup.as_empty(),
            spr_palette_group if spr_palette_group is not None else MutablePaletteGroup.as_empty(),
        )

        layout = QHBoxLayout()
        layout.setSpacing(0)

        self.bg_widget = PaletteGroupEditor(self, self.model.background_palette_group)
        self.spr_widget = PaletteGroupEditor(self, self.model.sprite_palette_group)

        layout.addWidget(self.bg_widget)
        layout.addWidget(self.spr_widget)

        self.bg_widget.palette_group_changed.connect(lambda *_: self.on_palette_update())
        self.spr_widget.palette_group_changed.connect(lambda *_: self.on_palette_update())

        self.setLayout(layout)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({self.parent}, {self.model.tileset}, "
            + f"{self.model.background_index}, {self.model.sprite_index}, "
            + f"{self.model.background_palette_group}, {self.model.sprite_palette_group})"
        )

    def load_from_level(self, level: Level):
        self.model.tileset = level.object_set_number
        self.model.background_index = level.object_palette_index
        self.model.sprite_index = level.enemy_palette_index
        self.model.restore()
        self._changed = False
        self.silent_update()

    def restore(self):
        self.model.restore()
        self.model.soft_save()
        self._changed = False
        self.silent_update()

    def save(self, rom: ROM | None = None):
        self.model.save(rom)
        self._changed = False

    def silent_update(self):
        self.bg_widget._palette_group = self.model.background_palette_group
        self.bg_widget._update()
        self.spr_widget._palette_group = self.model.sprite_palette_group
        self.spr_widget._update()

    @property
    def changed(self) -> bool:
        return self.model.changed

    @changed.setter
    def changed(self, value: bool):
        self.model.changed = value

    def on_palette_update(self):
        self.model.background_palette_group = self.bg_widget.palette_group
        self.model.sprite_palette_group = self.spr_widget.palette_group
        self.changed = True
        self.model.soft_save()
        self.palette_group_changed.emit(self.model.background_palette_group, self.model.sprite_palette_group)
