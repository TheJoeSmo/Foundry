from functools import cache
from typing import Protocol

from attr import attrs
from PySide6.QtGui import QColor

from foundry import root_dir
from foundry.game.File import ROM
from foundry.smb3parse.constants import Palette_By_Tileset, PalSet_Maps
from foundry.smb3parse.levels import BASE_OFFSET

MAP_PALETTE_ADDRESS = PalSet_Maps

PRG_SIZE = 0x2000
PALETTE_PRG_NO = 22

PALETTE_BASE_ADDRESS = BASE_OFFSET + PALETTE_PRG_NO * PRG_SIZE
PALETTE_OFFSET_LIST = Palette_By_Tileset
PALETTE_OFFSET_SIZE = 2  # bytes

PALETTE_GROUPS_PER_OBJECT_SET = 8
ENEMY_PALETTE_GROUPS_PER_OBJECT_SET = 4
PALETTES_PER_PALETTES_GROUP = 4

COLORS_PER_PALETTE = 4
COLOR_SIZE = 1  # byte

PALETTE_DATA_SIZE = (
    (PALETTE_GROUPS_PER_OBJECT_SET + ENEMY_PALETTE_GROUPS_PER_OBJECT_SET)
    * PALETTES_PER_PALETTES_GROUP
    * COLORS_PER_PALETTE
)


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
            A Palette filled with default values.
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
            The Palette that represents the absolute address in ROM.
        """
        return cls([int(i) for i in ROM().read(address, COLORS_PER_PALETTE)])

    @property
    def colors(self) -> list[QColor]:
        return [NESPalette[c & 0x3F] for c in self.color_indexes]


@cache
def get_internal_palette_offset(tileset: int) -> int:
    """
    Provides the absolute internal position of the palette group offset from ROM.

    Parameters
    ----------
    tileset : int
        The tileset to find the absolute internal position of.

    Returns
    -------
    int
        The absolute internal position of the tileset's palette group.
    """
    return PALETTE_BASE_ADDRESS + ROM().little_endian(PALETTE_OFFSET_LIST + (tileset * PALETTE_OFFSET_SIZE))


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


palette_file = root_dir.joinpath("data", "Default.pal")

with open(palette_file, "rb") as f:
    color_data = f.read()

offset = 0x18  # first color position

NESPalette: list[QColor] = []
COLOR_COUNT = 64
BYTES_IN_COLOR = 3 + 1  # bytes + separator

for i in range(COLOR_COUNT):
    NESPalette.append(QColor(color_data[offset], color_data[offset + 1], color_data[offset + 2]))

    offset += BYTES_IN_COLOR
