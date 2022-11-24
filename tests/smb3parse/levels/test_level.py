from foundry.core.geometry import Point
from foundry.game.File import ROM
from foundry.smb3parse.levels.level import Level
from foundry.smb3parse.levels.WorldMapPosition import WorldMapPosition


def test_level_1_1(rom_singleton: ROM, world_1):
    position_of_1_1 = WorldMapPosition(world_1, 1, Point(4, 0))

    level_1_1_from_map = Level.from_world_map(rom_singleton, position_of_1_1)
    level_1_1_from_memory = Level.from_memory(rom_singleton, 0x1, 0x1FB92, 0xC537)

    assert level_1_1_from_map == level_1_1_from_memory
