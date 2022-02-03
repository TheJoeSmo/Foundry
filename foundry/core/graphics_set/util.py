from foundry.core.graphics_set.GraphicsPage import GraphicalPage, GraphicalPageProtocol
from foundry.game.File import ROM
from foundry.smb3parse.constants import Level_BG_Pages1, Level_BG_Pages2

CHR_ROM_OFFSET = 0x40010
CHR_ROM_SEGMENT_SIZE = 0x400

WORLD_MAP = 0
SPADE_ROULETTE = 16
N_SPADE = 17
VS_2P = 18
HILLY = 3
CORRECTED_HILLY = 3
UNDERGROUND = 14
CORRECTED_UNDERGROUND = 19

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


def get_graphics_pages_from_tileset(tileset: int) -> tuple[GraphicalPageProtocol, ...]:
    if tileset == WORLD_MAP:
        return (
            GraphicalPage(0x14),
            GraphicalPage(0x15),
            GraphicalPage(0x16),
            GraphicalPage(0x17),
            GraphicalPage(0x20),
            GraphicalPage(0x21),
            GraphicalPage(0x22),
            GraphicalPage(0x23),
        )
    if tileset not in range(BG_PAGE_COUNT):
        return (
            GraphicalPage(tileset),
            GraphicalPage(tileset + 1),
            GraphicalPage(tileset + 2),
            GraphicalPage(tileset + 3),
        )
    if tileset == HILLY:
        tileset = CORRECTED_HILLY
    if tileset == UNDERGROUND:
        tileset = CORRECTED_UNDERGROUND

    graphic_page_index_1 = ROM().bulk_read(BG_PAGE_COUNT, Level_BG_Pages1)
    graphic_page_index_2 = ROM().bulk_read(BG_PAGE_COUNT, Level_BG_Pages2)
    pages = [
        GraphicalPage(graphic_page_index_1[tileset]),
        GraphicalPage(graphic_page_index_1[tileset] + 1),
        GraphicalPage(graphic_page_index_2[tileset]),
        GraphicalPage(graphic_page_index_2[tileset] + 1),
    ]

    if tileset == SPADE_ROULETTE:
        pages.extend([GraphicalPage(0x20), GraphicalPage(0x21), GraphicalPage(0x22), GraphicalPage(0x23)])
    elif tileset == N_SPADE:
        pages.extend([GraphicalPage(0x28), GraphicalPage(0x29), GraphicalPage(0x5A), GraphicalPage(0x31)])
    elif tileset == VS_2P:
        pages.extend([GraphicalPage(0x04), GraphicalPage(0x05), GraphicalPage(0x06), GraphicalPage(0x07)])
    else:
        pages.extend([GraphicalPage(0x00), GraphicalPage(0x00), GraphicalPage(0x00), GraphicalPage(0x00)])

    return tuple(pages)
