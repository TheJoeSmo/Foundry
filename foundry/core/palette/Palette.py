from typing import Protocol

from attr import attrs
from PySide6.QtGui import QColor

from foundry.core.palette import (
    COLORS_PER_PALETTE,
    PALETTES_PER_PALETTES_GROUP,
    NESPalette,
)
from foundry.core.palette.util import get_internal_palette_offset
from foundry.game.File import ROM


class PaletteProtocol(Protocol):
    color_indexes: list[int]

    def __bytes__(self) -> bytes:
        ...

    def __getitem__(self, item: int) -> int:
        ...

    def __setitem__(self, key: int, value: int):
        ...

    @property
    def colors(self) -> list[QColor]:
        ...


class PaletteGroupProtocol(Protocol):
    palettes: list[PaletteProtocol]

    def __bytes__(self) -> bytes:
        ...

    def __getitem__(self, item: int) -> PaletteProtocol:
        ...

    def __setitem__(self, key: int, value: PaletteProtocol):
        ...

    @property
    def background_color(self) -> QColor:
        ...


@attrs(slots=True, auto_attribs=True)
class Palette:
    color_indexes: list[int]

    def __bytes__(self) -> bytes:
        return bytes([i & 0xFF for i in self.color_indexes])

    def __getitem__(self, item: int) -> int:
        return self.color_indexes[item]

    def __setitem__(self, key: int, value: int):
        self.color_indexes[key] = value

    @classmethod
    def as_empty(cls):
        """
        Makes an empty palette of default values

        Returns
        -------
        Palette
            A palette filled with default values.
        """
        return cls([0, 0, 0, 0])

    @classmethod
    def from_rom(cls, address: int):
        """
        Creates a palette from an absolute address in ROM.

        Parameters
        ----------
        address : int
            The absolute address into the ROM.

        Returns
        -------
        Palette
            The palette that represents the absolute address in ROM.
        """
        return cls([int(i) for i in ROM().read(address, COLORS_PER_PALETTE)])

    @property
    def colors(self) -> list[QColor]:
        return [NESPalette[c & 0x3F] for c in self.color_indexes]


@attrs(slots=True, auto_attribs=True)
class PaletteGroup:
    palettes: list[PaletteProtocol]

    def __bytes__(self) -> bytes:
        b = bytearray()
        for palette in self.palettes:
            b.extend(bytes(palette))
        return bytes(b)

    def __getitem__(self, item: int) -> PaletteProtocol:
        return self.palettes[item]

    def __setitem__(self, key: int, value: PaletteProtocol):
        self.palettes[key] = value

    @property
    def background_color(self) -> QColor:
        return self.palettes[0].colors[0]

    @classmethod
    def as_empty(cls):
        """
        Makes an empty palette group of default values

        Returns
        -------
        PaletteGroup
            A PaletteGroup filled with default values.
        """
        return cls([Palette.as_empty() for _ in range(PALETTES_PER_PALETTES_GROUP)])

    @classmethod
    def from_rom(cls, address: int):
        """
        Creates a palette group from an absolute address in ROM.

        Parameters
        ----------
        address : int
            The absolute address into the ROM.

        Returns
        -------
        PaletteGroup
            The PaletteGroup that represents the absolute address in ROM.
        """
        return cls(
            [
                Palette.from_rom(address + offset)
                for offset in [COLORS_PER_PALETTE * i for i in range(PALETTES_PER_PALETTES_GROUP)]
            ]
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
        PaletteGroup
            The PaletteGroup that represents the tileset's palette group at the provided offset.
        """
        offset = get_internal_palette_offset(tileset) + index * PALETTES_PER_PALETTES_GROUP * COLORS_PER_PALETTE
        return cls.from_rom(offset)
