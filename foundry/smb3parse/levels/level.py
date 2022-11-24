from collections.abc import MutableSequence
from typing import Optional

from foundry.smb3parse.levels import HEADER_LENGTH, LevelBase
from foundry.smb3parse.levels.level_header import LevelHeader
from foundry.smb3parse.objects.tileset import ensure_tileset


class Level(LevelBase):
    def __init__(self, data: MutableSequence[int], tileset_number: int, layout_address: int, enemy_address: int):
        super().__init__(tileset_number, layout_address)

        self.tileset_number = tileset_number
        self.enemy_address = enemy_address

        self.world_map_position = None

        self.data = data

        self.header_address = self.layout_address - HEADER_LENGTH

        self.header_bytes: MutableSequence[int] = self.data[self.header_address : self.header_address + HEADER_LENGTH]

        self.header = LevelHeader(self.header_bytes, self.tileset_number)

    def set_world_map_position(self, point):
        self.world_map_position = point

    def __eq__(self, other):
        if not isinstance(other, Level):
            return False

        return (
            self.tileset_number == other.tileset_number
            and self.layout_address == other.layout_address
            and self.enemy_address == other.enemy_address
        )

    @staticmethod
    def from_world_map(data: MutableSequence[int], world_map_position) -> Optional["Level"]:
        level_info = world_map_position.level_info

        if level_info is None:
            return None

        tileset_number, layout_address, enemy_address = level_info

        level = Level(data, tileset_number, layout_address, enemy_address)

        level.set_world_map_position(world_map_position)

        return level

    @staticmethod
    def from_memory(data: MutableSequence[int], tileset_number: int, layout_address: int, enemy_address: int):
        ensure_tileset(tileset_number)

        level = Level(data, tileset_number, layout_address, enemy_address)

        return level
