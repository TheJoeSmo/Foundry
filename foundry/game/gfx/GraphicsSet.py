from itertools import chain
from typing import Protocol

from attr import attrs

from foundry.game.File import ROM
from foundry.smb3parse.constants import Level_BG_Pages1, Level_BG_Pages2

CHR_ROM_OFFSET = 0x40010
CHR_ROM_SEGMENT_SIZE = 0x400

WORLD_MAP = 0
SPADE_ROULETTE = 16
N_SPADE = 17
VS_2P = 18

BG_PAGE_COUNT = Level_BG_Pages2 - Level_BG_Pages1  # 23 in stock rom

GRAPHIC_SET_NAMES = [
    "Mario graphics (1)",
    "Plain",
    "Dungeon",
    "Underground (1)",
    "Sky",
    "Pipe/Water (1, Piranha Plant)",
    "Pipe/Water (2, Water)",
    "Mushroom house (1)",
    "Pipe/Water (3, Pipe)",
    "Desert",
    "Ship",
    "Giant",
    "Ice",
    "Clouds",
    "Underground (2)",
    "Spade bonus room",
    "Spade bonus",
    "Mushroom house (2)",
    "Pipe/Water (4)",
    "Hills",
    "Plain 2",
    "Tank",
    "Castle",
    "Mario graphics (2)",
    "Animated graphics (1)",
    "Animated graphics (2)",
    "Animated graphics (3)",
    "Animated graphics (4)",
    "Animated graphics (P-Switch)",
    "Game font/Course Clear graphics",
    "Animated graphics (5)",
    "Animated graphics (6)",
]


class GraphicalPageProtocol(Protocol):
    """
    A representation of a single page of graphics inside the ROM.

    Attributes
    ----------
    index: int
        The index of the graphical page into the ROM.
    """

    index: int

    def __bytes__(self) -> bytes:
        ...


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class GraphicalPage:
    """
    A representation of a single page of graphics inside the ROM, that uses ``attrs`` to create a
    basic implementation.

    Attributes
    ----------
    index: int
        The index of the graphical page into the ROM.
    """

    index: int

    @property
    def rom_offset(self) -> int:
        return CHR_ROM_OFFSET + self.index * CHR_ROM_SEGMENT_SIZE

    def __bytes__(self) -> bytes:
        return bytes(ROM().bulk_read(CHR_ROM_SEGMENT_SIZE, self.rom_offset))


class GraphicsSetProtocol(Protocol):
    """
    A representation of a series of graphical pages inside the ROM.

    Attributes
    ----------
    pages: tuple[GraphicalPageProtocol, ...]
        The pages that compose the graphical set.
    """

    pages: tuple[GraphicalPageProtocol, ...]

    def __bytes__(self) -> bytes:
        ...


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class GraphicsSet:
    """
    A representation of a series of graphical pages inside the ROM, that uses ``attrs`` to create
    a basic implementation.

    Attributes
    ----------
    pages: tuple[GraphicalPageProtocol, ...]
        The pages that compose the graphical set.
    """

    pages: tuple[GraphicalPageProtocol, ...]

    def __bytes__(self) -> bytes:
        return bytes(chain.from_iterable([bytes(page) for page in self.pages]))

    @classmethod
    def from_tileset(cls, index: int):
        cls.number = index
        if index == WORLD_MAP:
            return cls(
                (
                    GraphicalPage(0x14),
                    GraphicalPage(0x15),
                    GraphicalPage(0x16),
                    GraphicalPage(0x17),
                    GraphicalPage(0x20),
                    GraphicalPage(0x21),
                    GraphicalPage(0x22),
                    GraphicalPage(0x23),
                )
            )
        if index not in range(BG_PAGE_COUNT):
            return cls(
                (GraphicalPage(index), GraphicalPage(index + 1), GraphicalPage(index + 2), GraphicalPage(index + 3))
            )

        graphic_page_index_1 = ROM().bulk_read(BG_PAGE_COUNT, Level_BG_Pages1)
        graphic_page_index_2 = ROM().bulk_read(BG_PAGE_COUNT, Level_BG_Pages2)
        pages = [
            GraphicalPage(graphic_page_index_1[index]),
            GraphicalPage(graphic_page_index_1[index] + 1),
            GraphicalPage(graphic_page_index_2[index]),
            GraphicalPage(graphic_page_index_2[index] + 1),
        ]

        if index == SPADE_ROULETTE:
            pages.extend([GraphicalPage(0x20), GraphicalPage(0x21), GraphicalPage(0x22), GraphicalPage(0x23)])
        elif index == N_SPADE:
            pages.extend([GraphicalPage(0x28), GraphicalPage(0x29), GraphicalPage(0x5A), GraphicalPage(0x31)])
        elif index == VS_2P:
            pages.extend([GraphicalPage(0x04), GraphicalPage(0x05), GraphicalPage(0x06), GraphicalPage(0x07)])
        else:
            pages.extend([GraphicalPage(0x00), GraphicalPage(0x00), GraphicalPage(0x00), GraphicalPage(0x00)])

        return cls(tuple(pages))
