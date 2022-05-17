from __future__ import annotations

from collections.abc import Iterator

from attr import attrs
from pydantic import BaseModel
from PySide6.QtGui import QColor

from foundry.core.palette import COLORS_PER_PALETTE, PALETTES_PER_PALETTES_GROUP
from foundry.core.palette.Palette import Palette
from foundry.core.palette.util import get_internal_palette_offset


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class PaletteGroup:
    """
    A concrete implementation of a hashable and immutable group of palettes.
    """

    palettes: tuple[Palette, ...] = (Palette(), Palette(), Palette(), Palette())

    def __bytes__(self) -> bytes:
        b = bytearray()
        for palette in self.palettes:
            b.extend(bytes(palette))
        return bytes(b)

    def __getitem__(self, item: int) -> Palette:
        return self.palettes[item]

    def __iter__(self) -> Iterator[Palette]:
        return iter(self.palettes)

    @property
    def background_color(self) -> QColor:
        return self.palettes[0].colors[0]

    @classmethod
    def from_rom(cls, address: int) -> PaletteGroup:
        """
        Creates a palette group from an absolute address in ROM.

        Parameters
        ----------
        address : int
            The absolute address into the ROM.

        Returns
        -------
        PaletteGroup
            The palette group that represents the absolute address in ROM.
        """
        return cls(
            tuple(
                Palette.from_rom(address + offset)
                for offset in [COLORS_PER_PALETTE * i for i in range(PALETTES_PER_PALETTES_GROUP)]
            )
        )

    @classmethod
    def from_tileset(cls, tileset: int, index: int):
        """
        Loads a palette group from a tileset with a given index.

        Parameters
        ----------
        tileset : int
            The index of the tileset.
        index : int
            The index of the palette group inside the tileset.

        Returns
        -------
        Palette
            The PaletteGroup that represents the tileset's palette group at the provided offset.
        """
        offset = get_internal_palette_offset(tileset) + index * PALETTES_PER_PALETTES_GROUP * COLORS_PER_PALETTE
        return cls.from_rom(offset)


class PydanticPaletteGroup(BaseModel):
    """
    A generic representation of :class:`~foundry.core.palette.PaletteGroup.PaletteGroup`.

    Attributes
    ----------
    palettes: list[Palette]
        The palettes that compose the palette group.
    """

    palettes: list[Palette]

    @property
    def palette_protocols(self) -> list[Palette]:
        return self.palettes

    @property
    def palette_group(self) -> PaletteGroup:
        return PaletteGroup(tuple(self.palette_protocols))
