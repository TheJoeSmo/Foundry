from typing import Optional

from attr import attrs

from foundry.game.File import ROM
from foundry.game.gfx.Palette import (
    COLORS_PER_PALETTE,
    PALETTE_GROUPS_PER_OBJECT_SET,
    PALETTES_PER_PALETTES_GROUP,
    PaletteGroup,
    PaletteGroupProtocol,
    get_internal_palette_offset,
)


@attrs(slots=True, auto_attribs=True)
class PaletteGroupModel:
    tileset: int
    background_index: int
    sprite_index: int
    background_palette_group: PaletteGroupProtocol
    sprite_palette_group: PaletteGroupProtocol
    changed: bool = False
    background_palette_group_backup: Optional[PaletteGroupProtocol] = None
    sprite_palette_group_backup: Optional[PaletteGroupProtocol] = None

    def restore(self):
        self.background_palette_group = (
            self.background_palette_group_backup
            if self.background_palette_group_backup is not None
            else PaletteGroup.from_tileset(self.tileset, self.background_index)
        )
        self.sprite_palette_group = (
            self.sprite_palette_group_backup
            if self.sprite_palette_group_backup is not None
            else PaletteGroup.from_tileset(self.tileset, self.sprite_index + PALETTE_GROUPS_PER_OBJECT_SET)
        )

    def soft_save(self):
        if self.background_palette_group_backup is None:
            self.background_palette_group_backup = PaletteGroup.from_tileset(self.tileset, self.background_index)
        if self.sprite_palette_group_backup is None:
            self.sprite_palette_group_backup = PaletteGroup.from_tileset(
                self.tileset, self.sprite_index + PALETTE_GROUPS_PER_OBJECT_SET
            )
        self._save()

    def save(self, rom: Optional[ROM] = None):
        self.background_palette_group_backup = None
        self.sprite_palette_group_backup = None
        self._save(rom)

    def _save(self, rom: Optional[ROM] = None):
        bg_offset = (
            get_internal_palette_offset(self.tileset)
            + self.background_index * PALETTES_PER_PALETTES_GROUP * COLORS_PER_PALETTE
        )
        spr_offset = (
            get_internal_palette_offset(self.tileset)
            + (self.sprite_index + PALETTE_GROUPS_PER_OBJECT_SET) * PALETTES_PER_PALETTES_GROUP * COLORS_PER_PALETTE
        )

        if rom is None:
            rom = ROM()
        rom.write(bg_offset, bytes(self.background_palette_group))
        rom.write(spr_offset, bytes(self.sprite_palette_group))
