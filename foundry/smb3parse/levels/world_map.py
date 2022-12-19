from collections import defaultdict
from collections.abc import Generator
from warnings import warn

from foundry.core import (
    FindableEndianMutableSequence,
    FindableEndianSequence,
    FindableSequence,
    Sequence,
)
from foundry.core.geometry import Point
from foundry.smb3parse.constants import (
    TILE_BOWSER_CASTLE,
    TILE_CASTLE_BOTTOM,
    TILE_DUNGEON_1,
    TILE_DUNGEON_2,
    TILE_HAND_TRAP,
    TILE_LEVEL_1,
    TILE_LEVEL_10,
    TILE_MUSHROOM_HOUSE_1,
    TILE_MUSHROOM_HOUSE_2,
    TILE_PIPE,
    TILE_POND,
    TILE_PYRAMID,
    TILE_QUICKSAND,
    TILE_SPADE_HOUSE,
    TILE_SPIRAL_TOWER_1,
    TILE_SPIRAL_TOWER_2,
    TILE_STAR_1,
    TILE_STAR_2,
)
from foundry.smb3parse.levels import (
    BASE_OFFSET,
    COMPLETABLE_LIST_END_MARKER,
    COMPLETABLE_TILES_LIST,
    ENEMY_BASE_OFFSET,
    FIRST_VALID_ROW,
    LAYOUT_LIST_OFFSET,
    LEVEL_ENEMY_LIST_OFFSET,
    LEVEL_X_POS_LISTS,
    LEVEL_Y_POS_LISTS,
    LEVELS_IN_WORLD_LIST_OFFSET,
    OFFSET_BY_OBJECT_SET_A000,
    OFFSET_SIZE,
    SPECIAL_ENTERABLE_TILE_AMOUNT,
    SPECIAL_ENTERABLE_TILES_LIST,
    STRUCTURE_DATA_OFFSETS,
    TILE_ATTRIBUTES_TS0_OFFSET,
    VALID_COLUMNS,
    VALID_ROWS,
    WORLD_COUNT,
    WORLD_MAP_BASE_OFFSET,
    WORLD_MAP_HEIGHT,
    WORLD_MAP_SCREEN_SIZE,
    WORLD_MAP_SCREEN_WIDTH,
    LevelBase,
)
from foundry.smb3parse.levels.level import Level
from foundry.smb3parse.levels.WorldMapPosition import WorldMapPosition
from foundry.smb3parse.objects.tileset import WORLD_MAP_OBJECT_SET

TILE_NAMES = defaultdict(lambda: "NO NAME")
TILE_NAMES.update(
    {
        TILE_MUSHROOM_HOUSE_1: "Mushroom House",
        TILE_MUSHROOM_HOUSE_2: "Mushroom House",
        TILE_SPIRAL_TOWER_1: "Spiral Tower",
        TILE_SPIRAL_TOWER_2: "Spiral Tower",
        TILE_DUNGEON_1: "Dungeon",
        TILE_DUNGEON_2: "Dungeon",
        TILE_QUICKSAND: "Quicksand",
        TILE_PYRAMID: "Pyramid",
        TILE_PIPE: "Pipe",
        TILE_POND: "Pond",
        TILE_CASTLE_BOTTOM: "Peach's Castle",
        TILE_BOWSER_CASTLE: "Bowser's Lair",
        TILE_HAND_TRAP: "Hand Trap",
        TILE_SPADE_HOUSE: "Spade Bonus",
        TILE_STAR_1: "Star",
        TILE_STAR_2: "Star",
    }
)


def list_world_map_addresses(data: FindableEndianSequence[int]) -> list[int]:
    offsets: Sequence[int] = data[LAYOUT_LIST_OFFSET : LAYOUT_LIST_OFFSET + WORLD_COUNT * OFFSET_SIZE]
    addresses: list[int] = []

    for world in range(WORLD_COUNT):
        index: int = world * 2
        world_map_offset: int = (offsets[index + 1] << 8) + offsets[index]
        addresses.append(WORLD_MAP_BASE_OFFSET + world_map_offset)

    return addresses


def get_all_world_maps(data: FindableEndianMutableSequence[int]) -> list["WorldMap"]:
    world_map_addresses: list[int] = list_world_map_addresses(data)
    return [WorldMap(address, data) for address in world_map_addresses]


class WorldMap(LevelBase):
    """
    Represents the data associated with a world map/overworld. World maps are always 9 blocks high and 16 blocks wide.
    They can be multiple screens big, which are either not visibly connected or connected horizontally.

    Attributes:
        layout_address  The point in the ROM of the bytes making up the visual layout of the world map.
        layout_bytes    The actual bytes making up the visual layout

        width           The width of the world map in blocks across all scenes.
        height          The height of the world map, always 9 blocks.

        tileset      An Tileset object for the world map object set.
        screen_count    How many screens this world map spans.
    """

    def __init__(self, layout_address: int, data: FindableEndianMutableSequence[int]):
        super().__init__(WORLD_MAP_OBJECT_SET, layout_address)

        self.data: FindableEndianMutableSequence[int] = data

        self._minimal_enterable_tiles = _get_normal_enterable_tiles(self.data)
        self._special_enterable_tiles = _get_special_enterable_tiles(self.data)
        self._completable_tiles = _get_completable_tiles(self.data)

        memory_addresses = list_world_map_addresses(self.data)

        try:
            self.number = memory_addresses.index(layout_address) + 1
        except ValueError:
            raise ValueError(f"World map was not found at given memory address {hex(layout_address)}.")

        self.height = WORLD_MAP_HEIGHT

        layout_end_index = data.find(b"\xFF", layout_address)
        self.layout_bytes = data[layout_address:layout_end_index]

        if len(self.layout_bytes) % WORLD_MAP_SCREEN_SIZE != 0:
            raise ValueError(
                f"Invalid length of layout bytes for world map ({self.layout_bytes}). "
                f"Should be divisible by {WORLD_MAP_SCREEN_SIZE}."
            )

        self.screen_count = len(self.layout_bytes) // WORLD_MAP_SCREEN_SIZE
        self.width = int(self.screen_count * WORLD_MAP_SCREEN_WIDTH)

        self._parse_structure_data_block(data)

    @property
    def world_index(self):
        return self.number - 1

    @property
    def level_count(self):
        return self.level_count_s1 + self.level_count_s2 + self.level_count_s3 + self.level_count_s4

    def _parse_structure_data_block(self, data: FindableEndianSequence):
        structure_block_offset: int = data.endian(STRUCTURE_DATA_OFFSETS + OFFSET_SIZE * self.world_index)

        self.structure_block_start = WORLD_MAP_BASE_OFFSET + structure_block_offset

        # the indexes into the y_pos list, where the levels for the n-th screen start
        y_pos_start_by_screen: Sequence[int] = data[self.structure_block_start : self.structure_block_start + 4]

        level_y_pos_list_start: int = WORLD_MAP_BASE_OFFSET + data.endian(
            LEVEL_Y_POS_LISTS + OFFSET_SIZE * self.world_index
        )
        level_x_pos_list_start: int = WORLD_MAP_BASE_OFFSET + data.endian(
            LEVEL_X_POS_LISTS + OFFSET_SIZE * self.world_index
        )

        level_y_pos_list_end = level_x_pos_list_start - level_y_pos_list_start

        self.level_count_s1 = y_pos_start_by_screen[1] - y_pos_start_by_screen[0]
        self.level_count_s2 = y_pos_start_by_screen[2] - y_pos_start_by_screen[1]
        self.level_count_s3 = y_pos_start_by_screen[3] - y_pos_start_by_screen[2]
        self.level_count_s4 = level_y_pos_list_end - y_pos_start_by_screen[3]

    def level_for_position(self, screen: int, point: Point) -> tuple[int, int, int] | None:
        """
        The rom takes the point of the current player, so the world, the screen and the x and y coordinates, and
        operates on them. First it is checked, whether or not the player is located on a tile, that is able to be
        entered.

        If that is the case, the x and y coordinates are used to look up the object set and address of the level. The
        object set is necessary to find the right base offset for the level address and to correctly parse its object
        data.

        Using the tile information it should be possible to correctly name almost all levels, for example Level 1 will
        be located in the list at the offset pointed to by the "Level 1" tile in that world.

        That means, that all levels should be able to be collected, by iterating over all possible tiles and following
        the same procedure as the rom.

        Parameters
        ----------
        screen : int
            The screen index of the level to acquire.
        point: Point
            The point the player is located at.

        Returns
        -------
        Any
            A tuple of the object set number, the absolute level address, pointing to the objects and the enemy
        address. Or None, if there is no level at the map point.
        """
        assert isinstance(screen, int)
        assert isinstance(point, Point)

        tile = self.tile_at(screen, point)

        if tile in [TILE_SPADE_HOUSE, TILE_MUSHROOM_HOUSE_1, TILE_MUSHROOM_HOUSE_2]:
            warn("Spade and mushroom house currently not supported, when getting a level address.")
            return None

        if not self.is_enterable(tile):
            return None

        level_indexes = self.level_indexes(WorldMapPosition(None, screen, point))
        if level_indexes is None:
            return None

        point_address, level_offset_address, enemy_offset_address = level_indexes

        level_offset = self.data.endian(level_offset_address, size=2)

        assert 0xA000 <= level_offset < 0xC000, level_offset  # suppose that level layouts are only in this range?

        correct_row_value = self.data.endian(point_address.y, size=1)
        tileset_number = correct_row_value & 0x0F

        tileset_offset = (self.data.endian(OFFSET_BY_OBJECT_SET_A000 + tileset_number, size=1) * 2 - 10) * 0x1000

        absolute_level_address = 0x0010 + tileset_offset + level_offset

        # get enemy address
        enemy_address = ENEMY_BASE_OFFSET + self.data.endian(enemy_offset_address)

        return tileset_number, absolute_level_address, enemy_address

    def replace_level_at_position(self, level_info, point: WorldMapPosition):
        level_address, enemy_address, tileset_number = level_info

        existing_level = self.level_for_position(point.screen, point.point)

        if existing_level is None:
            raise LookupError("No existing level at point.")

        level_index = self.level_indexes(point)
        assert level_index is not None
        level_point, level_offset_address, enemy_offset_address = level_index

        row_value: int = ((point.point.y + FIRST_VALID_ROW) << 4) + tileset_number
        self.data[level_point.y] = row_value

        column_value: int = ((point.screen - 1) << 4) + point.point.x
        self.data[level_point.x] = column_value

        tileset_offset = (self.data[OFFSET_BY_OBJECT_SET_A000 + tileset_number] * 2 - 10) * 0x1000
        level_offset = level_address - tileset_offset - BASE_OFFSET
        self.data[level_offset_address : level_offset_address + 1] = self.data.from_endian(level_offset)

        enemy_offset = enemy_address - BASE_OFFSET
        self.data[enemy_offset_address : enemy_offset_address + 1] = self.data.from_endian(enemy_offset)

    def level_indexes(self, point: WorldMapPosition) -> tuple[Point, int, int] | None:
        """
        Provide the level index from a given screen and point.

        Parameters
        ----------
        point: WorldMapPosition
            The point inside the world map.

        Returns
        -------
        tuple[Point, int, int] | None
            The level indexes, if it exists.
        """
        level_y_pos_list_start: int = WORLD_MAP_BASE_OFFSET + self.data.endian(
            LEVEL_Y_POS_LISTS + OFFSET_SIZE * self.world_index
        )
        level_x_pos_list_start: int = WORLD_MAP_BASE_OFFSET + self.data.endian(
            LEVEL_X_POS_LISTS + OFFSET_SIZE * self.world_index
        )

        row_amount = col_amount = level_x_pos_list_start - level_y_pos_list_start

        row_start_index = sum(
            [self.level_count_s1, self.level_count_s2, self.level_count_s3, self.level_count_s4][0 : point.screen - 1]
        )

        # find the row point
        for row_index in range(row_start_index, row_amount):
            value: int = self.data.endian(level_y_pos_list_start + row_index, size=1)

            # adjust the value, so that we ignore the black border tiles around the map
            row = (value >> 4) - FIRST_VALID_ROW

            if row == point.point.y:
                break
        else:
            # no level on row of player
            return None

        for col_index in range(row_index, col_amount):
            column: int = self.data.endian(level_x_pos_list_start + col_index, size=1) & 0x0F

            if column == point.point.x:
                break
        else:
            # no column for row
            return None

        point_: Point = Point(level_x_pos_list_start + col_index, level_y_pos_list_start + col_index)

        # get level offset
        level_list_offset_position: int = LEVELS_IN_WORLD_LIST_OFFSET + self.world_index * OFFSET_SIZE
        level_list_address: int = WORLD_MAP_BASE_OFFSET + self.data.endian(level_list_offset_position)

        level_offset_position: int = level_list_address + OFFSET_SIZE * col_index

        enemy_list_start_offset: int = LEVEL_ENEMY_LIST_OFFSET + self.world_index * OFFSET_SIZE
        enemy_list_start: int = WORLD_MAP_BASE_OFFSET + self.data.endian(enemy_list_start_offset)

        enemy_offset_position: int = enemy_list_start + col_index * OFFSET_SIZE

        return point_, level_offset_position, enemy_offset_position

    def level_name_for_position(self, screen: int, point: Point) -> str:
        tile = self.tile_at(screen, point)

        if not self.is_enterable(tile):
            return ""

        if tile in range(TILE_LEVEL_1, TILE_LEVEL_10 + 1):
            return f"Level {self.number}-{tile - TILE_LEVEL_1 + 1}"

        return f"Level {self.number}-{TILE_NAMES[tile]}"

    def tile_at(self, screen: int, point: Point) -> int:
        """
        Returns the tile value at the given coordinates. We define (0, 0) to be the topmost, leftmost tile, under the
        black border, so we'll adjust them accordingly, when bound checking.
        """
        assert isinstance(screen, int)
        assert isinstance(point, Point)

        if point.y + FIRST_VALID_ROW not in VALID_ROWS:
            raise ValueError(
                f"Given row {point.y} is outside the valid range for world maps. First valid row is "
                f"{FIRST_VALID_ROW}."
            )

        if point.x not in VALID_COLUMNS:
            raise ValueError(
                f"Given column {point.x} is outside the valid range for world maps. Remember the black " f"border."
            )

        if screen - 1 not in range(self.screen_count):
            raise ValueError(f"World {self.number} has {self.screen_count} screens. " f"Given number {screen} invalid.")

        return self.layout_bytes[(screen - 1) * WORLD_MAP_SCREEN_SIZE + point.y * WORLD_MAP_SCREEN_WIDTH + point.x]

    def is_enterable(self, tile_index: int) -> bool:
        """
        The tile attributes for the overworld tile set define the minimal value a tile has to have to be enterable.
        Which of the 4 bytes to check against depends on the "quadrant", so the 2 MSBs.

        :param tile_index: Tile index to check.

        :return: Whether the tile is enterable.
        """
        quadrant_index = tile_index >> 6

        # todo allows spade houses, but those break. treat them differently when loading their level
        return (
            tile_index >= self._minimal_enterable_tiles[quadrant_index]
            or tile_index in self._completable_tiles
            or tile_index in self._special_enterable_tiles
        )

    def gen_positions(self) -> Generator[WorldMapPosition, None, None]:
        """
        Returns a generator, which yield WorldMapPosition objects, one screen at a time, one row at a time.
        """

        for screen in range(1, self.screen_count + 1):
            for row in range(WORLD_MAP_HEIGHT):
                for column in range(WORLD_MAP_SCREEN_WIDTH):
                    yield WorldMapPosition(self, screen, Point(column, row))

    def gen_levels(self):
        """
        Returns a generator, which yields all levels accessible from this world map.
        """
        for point in self.gen_positions():
            level_info_tuple = self.level_for_position(point.screen, point.point)

            if level_info_tuple is None:
                continue

            else:
                yield Level(self.data, *level_info_tuple)

    @staticmethod
    def from_world_number(data: FindableEndianMutableSequence[int], world_number: int) -> "WorldMap":
        if not world_number - 1 in range(WORLD_COUNT):
            raise ValueError(f"World number must be between 1 and {WORLD_COUNT}, including.")

        memory_address = list_world_map_addresses(data)[world_number - 1]

        return WorldMap(memory_address, data)

    def __repr__(self):
        return f"World {self.number}"


def _get_normal_enterable_tiles(data: Sequence[int]) -> Sequence[int]:
    return data[TILE_ATTRIBUTES_TS0_OFFSET : TILE_ATTRIBUTES_TS0_OFFSET + 4]


def _get_special_enterable_tiles(data: Sequence[int]) -> Sequence[int]:
    return data[SPECIAL_ENTERABLE_TILES_LIST : SPECIAL_ENTERABLE_TILES_LIST + SPECIAL_ENTERABLE_TILE_AMOUNT]


def _get_completable_tiles(data: FindableSequence) -> Sequence[int]:
    completable_tile_amount: int = (
        data.find(COMPLETABLE_LIST_END_MARKER, COMPLETABLE_TILES_LIST) - COMPLETABLE_TILES_LIST
    )

    return data[COMPLETABLE_TILES_LIST : COMPLETABLE_TILES_LIST + completable_tile_amount]
