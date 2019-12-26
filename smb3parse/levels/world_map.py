from typing import List, Optional, Tuple

from smb3parse.levels import LevelBase
from smb3parse.levels.level import HEADER_LENGTH
from smb3parse.util.rom import Rom

OFFSET_SIZE = 2  # byte

BASE_OFFSET = 0x10  # the size of the rom header identifying the rom

ENEMY_BASE_OFFSET = BASE_OFFSET + 1
"""
One additional byte, at the beginning of every enemy data, where I don't know what does
"""

LEVEL_BASE_OFFSET = BASE_OFFSET + 0xE000
"""
Offset for a lot of world and level related parsing.
"""

LAYOUT_LIST_OFFSET = LEVEL_BASE_OFFSET + 0xA598

TILE_ATTRIBUTES_TS0_OFFSET = LEVEL_BASE_OFFSET + 0xA400
"""
The first 4 bytes describe minimal indexes an overworld tile must have to be enterable.
"""

STRUCTURE_DATA_OFFSETS = LEVEL_BASE_OFFSET + 0xB3CA  # Map_ByXHi_InitIndex
"""
This lists the start of a block of world meta data. 9 worlds means 9 times 2 bytes of offsets. The block starts with a
0x00, so that also marks the end of the block before it.
"""

LEVEL_Y_POS_LISTS = LEVEL_BASE_OFFSET + 0xB3DC  # Map_ByRowType
"""
This list contains the offsets to the y positions/row indexes of the levels of a world map. Since world maps can have up
to 4 screens, the offset could points to 4 consecutive lists, so we need to know the amount of levels per screen, to
make sense of them.
"""

LEVEL_X_POS_LISTS = LEVEL_BASE_OFFSET + 0xB3EE  # Map_ByScrCol
"""
This list contains the offsets to the x positions/column indexes of the levels in a world map. They are listed in a row
for all 4 screens.
"""

LEVEL_ENEMY_LIST_OFFSET = LEVEL_BASE_OFFSET + 0xB400
"""
"""

LEVELS_IN_WORLD_LIST_OFFSET = LEVEL_BASE_OFFSET + 0xB412
"""
The memory locations of levels inside a world map are listed in a row. This offset points to the memory locations of
these lists for every world. The first 2 bytes following this offset point to the levels in world 1, the next 2 for
world 2 etc.
"""

OFFSET_BY_OBJECT_SET_A000 = BASE_OFFSET + 0x34000 + 0x83E9  # PAGE_A000_ByTileset
"""
A list of values, which specify which ROM page should be loaded into addresses 0xA000 - 0xBFFF for a given object set.
This is necessary, since the ROM is larger then the addressable RAM in the NES. The offsets of levels are always into
the RAM, which means, to address levels at different parts in the ROM these parts need to be loaded into the RAM first.
"""

OFFSET_BY_OBJECT_SET_C000 = 0x34010 + 0x83D6  # PAGE_C000_ByTileset
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

WORLD_MAP_SCREEN_SIZE = WORLD_MAP_HEIGHT * WORLD_MAP_SCREEN_WIDTH  # bytes


def list_world_map_addresses(rom: Rom) -> List[int]:
    offsets = rom.read(LAYOUT_LIST_OFFSET, WORLD_COUNT * OFFSET_SIZE)

    addresses = []

    for world in range(WORLD_COUNT):
        index = world * 2

        world_map_offset = (offsets[index + 1] << 8) + offsets[index]

        addresses.append(LEVEL_BASE_OFFSET + world_map_offset)

    return addresses


def get_all_world_maps(rom: Rom) -> List["WorldMap"]:
    world_map_addresses = list_world_map_addresses(rom)

    return [WorldMap(address, rom) for address in world_map_addresses]


class WorldMap(LevelBase):
    """
    Represents the data associated with a world map/overworld. World maps are always 9 blocks high and 16 blocks wide.
    They can be multiple screens big, which are either not visibly connected or connected horizontally.

    Attributes:
        memory_address  The position in the ROM of the bytes making up the visual layout of the world map.
        layout_bytes    The actual bytes making up the visual layout

        width           The width of the world map in blocks across all scenes.
        height          The height of the world map, always 9 blocks.

        object_set      An ObjectSet object for the world map object set.
        screen_count    How many screens this world map spans.
    """

    def __init__(self, memory_address: int, rom: Rom):
        super(WorldMap, self).__init__(memory_address)

        self._rom = rom

        self._minimal_enterable_tiles = _get_enterable_tiles(self._rom)

        memory_addresses = list_world_map_addresses(rom)

        try:
            self.world_number = memory_addresses.index(memory_address) + 1
        except ValueError:
            raise ValueError(f"World map was not found at given memory address {hex(memory_address)}.")

        self._height = WORLD_MAP_HEIGHT

        layout_end_index = rom.find(b"\xFF", memory_address)

        self.layout_bytes = rom.read(memory_address, layout_end_index - memory_address)

        if len(self.layout_bytes) % WORLD_MAP_SCREEN_SIZE != 0:
            raise ValueError(
                f"Invalid length of layout bytes for world map ({self.layout_bytes}). "
                f"Should be divisible by {WORLD_MAP_SCREEN_SIZE}."
            )

        self.screen_count = len(self.layout_bytes) // WORLD_MAP_SCREEN_SIZE
        self._width = int(self.screen_count * WORLD_MAP_SCREEN_WIDTH)

        self._parse_structure_data_block(rom)

    @property
    def world_index(self):
        return self.world_number - 1

    @property
    def level_count(self):
        return self.level_count_s1 + self.level_count_s2 + self.level_count_s3 + self.level_count_s4

    def _parse_structure_data_block(self, rom: Rom):
        structure_block_offset = rom.little_endian(STRUCTURE_DATA_OFFSETS + OFFSET_SIZE * self.world_index)

        self.structure_block_start = LEVEL_BASE_OFFSET + structure_block_offset

        # the indexes into the y_pos list, where the levels for the n-th screen start
        y_pos_start_by_screen = rom.read(self.structure_block_start, 4)

        level_y_pos_list_start = LEVEL_BASE_OFFSET + rom.little_endian(
            LEVEL_Y_POS_LISTS + OFFSET_SIZE * self.world_index
        )

        level_x_pos_list_start = LEVEL_BASE_OFFSET + rom.little_endian(
            LEVEL_X_POS_LISTS + OFFSET_SIZE * self.world_index
        )

        level_y_pos_list_end = level_x_pos_list_start - level_y_pos_list_start

        self.level_count_s1 = y_pos_start_by_screen[1] - y_pos_start_by_screen[0]
        self.level_count_s2 = y_pos_start_by_screen[2] - y_pos_start_by_screen[1]
        self.level_count_s3 = y_pos_start_by_screen[3] - y_pos_start_by_screen[2]
        self.level_count_s4 = level_y_pos_list_end - y_pos_start_by_screen[3]

    def level_for_position(self, screen: int, player_row: int, player_column: int) -> Optional[Tuple[int, int, int]]:
        """
        The rom takes the position of the current player, so the world, the screen and the x and y coordinates, and
        operates on them. First it is checked, whether or not the player is located on a tile, that is able to be
        entered.

        If that is the case, the x and y coordinates are used to look up the object set and address of the level. The
        object set is necessary to find the right base offset for the level address and to correctly parse its object
        data.

        Using the tile information it should be possible to correctly name almost all levels, for example Level *-1 will
        be located in the list at the offset pointed to by the "Level 1" tile in that world.

        That means, that all levels should be able to be collected, by iterating over all possible tiles and following
        the same procedure as the rom.

        :param screen:
        :param player_row:
        :param player_column:

        :return: A tuple of the absolute level address, pointing to the objects, enemy address and the object set. Or
            None, if there is no level at the map position.
        """

        tile = self._map_tile_for_position(screen, player_row, player_column)

        if not self._is_enterable(tile):
            return None

        level_y_pos_list_start = LEVEL_BASE_OFFSET + self._rom.little_endian(
            LEVEL_Y_POS_LISTS + OFFSET_SIZE * self.world_index
        )

        level_x_pos_list_start = LEVEL_BASE_OFFSET + self._rom.little_endian(
            LEVEL_X_POS_LISTS + OFFSET_SIZE * self.world_index
        )

        row_amount = col_amount = level_x_pos_list_start - level_y_pos_list_start

        # find the row position
        for row_index in range(row_amount):
            value = self._rom.int(level_y_pos_list_start + row_index)

            # adjust the value, so that we ignore the black border tiles around the map
            row = (value >> 4) - FIRST_VALID_ROW

            if row == player_row:
                break
        else:
            # no level on row of player
            return None

        for col_index in range(row_index, col_amount):
            column = self._rom.int(level_x_pos_list_start + col_index) & 0x0F

            if column == player_column:
                break
        else:
            # no column for row
            return None

        level_index = col_index

        # get level offset
        level_list_offset_position = LEVELS_IN_WORLD_LIST_OFFSET + self.world_index * OFFSET_SIZE

        level_list_address = LEVEL_BASE_OFFSET + self._rom.little_endian(level_list_offset_position)

        level_offset = self._rom.little_endian(level_list_address + OFFSET_SIZE * level_index)

        assert 0xA000 <= level_offset < 0xC000  # suppose that level layouts are only in this range?

        # get object set offset

        # the object set is part of the row, but we didn't have the correct row index before, only the first match
        correct_row_value = self._rom.int(level_y_pos_list_start + level_index)
        object_set = correct_row_value & 0x0F

        object_set_offset = (self._rom.int(OFFSET_BY_OBJECT_SET_A000 + object_set) * 2 - 10) * 0x1000

        absolute_level_address = 0x0010 + object_set_offset + level_offset + HEADER_LENGTH

        # get enemy address

        enemy_list_start_offset = LEVEL_ENEMY_LIST_OFFSET + self.world_index * OFFSET_SIZE

        enemy_list_start = LEVEL_BASE_OFFSET + self._rom.little_endian(enemy_list_start_offset)

        enemy_address = ENEMY_BASE_OFFSET + self._rom.little_endian(enemy_list_start + level_index * OFFSET_SIZE)

        return absolute_level_address, enemy_address, object_set

    def _map_tile_for_position(self, screen: int, row: int, column: int) -> int:
        """
        Returns the tile value at the given coordinates. We (0, 0) to be the topmost, leftmost tile, under the black
        border, so we'll adjust them accordingly, when bound checking.

        :param screen:
        :param row:
        :param column:
        :return:
        """
        if row + FIRST_VALID_ROW not in VALID_ROWS:
            raise ValueError(
                f"Given row {row} is outside the valid range for world maps. First valid row is " f"{FIRST_VALID_ROW}."
            )

        if column not in VALID_COLUMNS:
            raise ValueError(
                f"Given column {column} is outside the valid range for world maps. Remember the black " f"border."
            )

        if screen - 1 not in range(self.screen_count):
            raise ValueError(
                f"World {self.world_number} has {self.screen_count} screens. " f"Given number {screen} invalid."
            )

        return self.layout_bytes[(screen - 1) * WORLD_MAP_SCREEN_SIZE + row * WORLD_MAP_SCREEN_WIDTH + column]

    def _is_enterable(self, tile_index: int) -> bool:
        """
        The tile attributes for the overworld tile set define the minimal value a tile has to have to be enterable.
        Which of the 4 bytes to check against depends on the "quadrant", so the 2 MSBs.

        :param tile_index: Tile index to check.

        :return: Whether the tile is enterable.
        """
        quadrant_index = tile_index >> 6

        return tile_index >= self._minimal_enterable_tiles[quadrant_index]

    @staticmethod
    def from_world_number(rom: Rom, world_number: int) -> "WorldMap":
        if not world_number - 1 in range(WORLD_COUNT):
            raise ValueError(f"World number must be between 1 and {WORLD_COUNT}, including.")

        memory_address = list_world_map_addresses(rom)[world_number - 1]

        return WorldMap(memory_address, rom)


def _get_enterable_tiles(rom: Rom) -> bytearray:
    return rom.read(TILE_ATTRIBUTES_TS0_OFFSET, 4)
