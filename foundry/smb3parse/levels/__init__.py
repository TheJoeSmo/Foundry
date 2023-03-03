from abc import ABC

from foundry.smb3parse.constants import (
    BASE_OFFSET,
    Level_TilesetIdx_ByTileset,
    Map_ByRowType,
    Map_ByScrCol,
    Map_ByXHi_InitIndex,
    Map_Completable_Tiles,
    Map_EnterSpecialTiles,
    Map_LevelLayouts,
    Map_ObjSets,
    Map_Tile_Layouts,
    PAGE_A000_ByTileset,
    PAGE_C000_ByTileset,
    Tile_Attributes_TS0,
)

OFFSET_SIZE = 2  # byte

ENEMY_BASE_OFFSET = BASE_OFFSET  # + 1
"""
One additional byte, at the beginning of every enemy data, where I don't know what does
"""

WORLD_MAP_BASE_OFFSET = BASE_OFFSET + 0xE000
"""
Offset for a lot of world related parsing.
"""

LEVEL_BASE_OFFSET = Level_TilesetIdx_ByTileset
"""
Offset for level related parsing. Currently only used in Header.
"""

LAYOUT_LIST_OFFSET = Map_Tile_Layouts

TILE_ATTRIBUTES_TS0_OFFSET = Tile_Attributes_TS0
"""
The first 4 bytes describe minimal indexes an overworld tile must have to be enterable.
"""

STRUCTURE_DATA_OFFSETS = Map_ByXHi_InitIndex
"""
This lists the start of a block of world meta data. 9 worlds means 9 times 2 bytes of offsets. The block starts with a
0x00, so that also marks the end of the block before it.
"""

LEVEL_Y_POS_LISTS = Map_ByRowType
"""
This list contains the offsets to the y positions/row indexes of the levels of a world map. Since world maps can have up
to 4 screens, the offset could points to 4 consecutive lists, so we need to know the amount of levels per screen, to
make sense of them.
"""

LEVEL_X_POS_LISTS = Map_ByScrCol
"""
This list contains the offsets to the x positions/column indexes of the levels in a world map. They are listed in a row
for all 4 screens.
"""

LEVEL_ENEMY_LIST_OFFSET = Map_ObjSets
"""
"""

LEVELS_IN_WORLD_LIST_OFFSET = Map_LevelLayouts
"""
The memory locations of levels inside a world map are listed in a row. This offset points to the memory locations of
these lists for every world. The first 2 bytes following this offset point to the levels in world 1, the next 2 for
world 2 etc.
"""

OFFSET_BY_OBJECT_SET_A000 = PAGE_A000_ByTileset
"""
A list of values, which specify which ROM page should be loaded into addresses 0xA000 - 0xBFFF for a given object set.
This is necessary, since the ROM is larger then the addressable RAM in the NES. The offsets of levels are always into
the RAM, which means, to address levels at different parts in the ROM these parts need to be loaded into the RAM first.
"""

OFFSET_BY_OBJECT_SET_C000 = PAGE_C000_ByTileset
"""
Same with the ROM page and addresses 0xC000 - 0xFFFF.
"""

WORLD_COUNT = 9  # includes warp zone

WORLD_MAP_HEIGHT = 9  # blocks
WORLD_MAP_SCREEN_WIDTH = 16  # blocks

FIRST_VALID_ROW = 2
"""
Tiles in rows before this one are part of the border and not valid overworld tiles.
"""

VALID_ROWS = range(FIRST_VALID_ROW, FIRST_VALID_ROW + WORLD_MAP_HEIGHT)
"""
A range of row values, where Mario could possibly stand.
"""

VALID_COLUMNS = range(WORLD_MAP_SCREEN_WIDTH)
"""
A range of column values, where Mario could possibly stand.
"""

COMPLETABLE_TILES_LIST = Map_Completable_Tiles
"""
A list of tile values, that are completable, like the Toad House.
"""

COMPLETABLE_LIST_END_MARKER = 0x00  # MCT_END
"""
A value, that specifies the end of the completable tiles, rather than a set address.
"""

SPECIAL_ENTERABLE_TILES_LIST = Map_EnterSpecialTiles
"""
A list of tile values, that are also enterable, like the castle and the toad house.
"""

SPECIAL_ENTERABLE_TILE_AMOUNT = 11  # the rom mistakenly uses 0x1A

WORLD_MAP_SCREEN_SIZE = WORLD_MAP_HEIGHT * WORLD_MAP_SCREEN_WIDTH  # bytes

# in bytes
HEADER_LENGTH = 9

# in blocks
LEVEL_MIN_LENGTH = 0x10
LEVEL_MAX_LENGTH = 0x100
LEVEL_LENGTH_INTERVAL = 0x10

DEFAULT_HORIZONTAL_HEIGHT = 27
DEFAULT_VERTICAL_WIDTH = 16


def is_valid_level_length(level_length: int) -> bool:
    """
    Check if a level length is valid.

    Parameters
    ----------
    level_length : int
        The length of the level in bytes.

    Returns
    -------
    bool
        True if the level length is valid, False otherwise.

    Notes
    -----
    A level length is considered valid if it is within the range of LEVEL_MIN_LENGTH
    and LEVEL_MAX_LENGTH, inclusive, and a multiple of LEVEL_LENGTH_INTERVAL.

    """
    return level_length in range(LEVEL_MIN_LENGTH, LEVEL_MAX_LENGTH + 1, LEVEL_LENGTH_INTERVAL)


class LevelBase(ABC):
    """
    Abstract base class for representing a level in Super Mario Bros 3.

    Attributes
    ----------
    width : int
        The width of the level in blocks.
    height : int
        The height of the level in blocks.
    layout_address : int
        The address of the level's layout in memory.
    tileset_number : int
        The tileset number of the level.
    """

    width: int
    height: int

    def __init__(self, tileset_number: int, layout_address: int) -> None:
        """
        Initializes a LevelBase object with the given tileset number and layout address.

        Parameters
        ----------
        tileset_number : int
            The tileset number of the level.
        layout_address : int
            The address of the level's layout in memory.
        """
        self.layout_address = layout_address
        self.tileset_number = tileset_number
