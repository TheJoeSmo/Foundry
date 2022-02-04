from foundry.core.graphics_page.GraphicsPage import GraphicsPage, GraphicsPageProtocol
from foundry.game.File import ROM
from foundry.smb3parse.constants import Level_BG_Pages1, Level_BG_Pages2

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


def get_graphics_pages_from_tileset(tileset: int) -> tuple[GraphicsPageProtocol, ...]:
    if tileset == WORLD_MAP:
        return (
            GraphicsPage(0x14),
            GraphicsPage(0x15),
            GraphicsPage(0x16),
            GraphicsPage(0x17),
            GraphicsPage(0x20),
            GraphicsPage(0x21),
            GraphicsPage(0x22),
            GraphicsPage(0x23),
        )
    if tileset not in range(BG_PAGE_COUNT):
        return (
            GraphicsPage(tileset),
            GraphicsPage(tileset + 1),
            GraphicsPage(tileset + 2),
            GraphicsPage(tileset + 3),
        )
    if tileset == HILLY:
        tileset = CORRECTED_HILLY
    if tileset == UNDERGROUND:
        tileset = CORRECTED_UNDERGROUND

    graphic_page_index_1 = ROM().bulk_read(BG_PAGE_COUNT, Level_BG_Pages1)
    graphic_page_index_2 = ROM().bulk_read(BG_PAGE_COUNT, Level_BG_Pages2)
    pages = [
        GraphicsPage(graphic_page_index_1[tileset]),
        GraphicsPage(graphic_page_index_1[tileset] + 1),
        GraphicsPage(graphic_page_index_2[tileset]),
        GraphicsPage(graphic_page_index_2[tileset] + 1),
    ]

    if tileset == SPADE_ROULETTE:
        pages.extend([GraphicsPage(0x20), GraphicsPage(0x21), GraphicsPage(0x22), GraphicsPage(0x23)])
    elif tileset == N_SPADE:
        pages.extend([GraphicsPage(0x28), GraphicsPage(0x29), GraphicsPage(0x5A), GraphicsPage(0x31)])
    elif tileset == VS_2P:
        pages.extend([GraphicsPage(0x04), GraphicsPage(0x05), GraphicsPage(0x06), GraphicsPage(0x07)])
    else:
        pages.extend([GraphicsPage(0x00), GraphicsPage(0x00), GraphicsPage(0x00), GraphicsPage(0x00)])

    return tuple(pages)
