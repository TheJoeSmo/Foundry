from foundry.core.geometry import Point
from foundry.game.File import ROM
from foundry.smb3parse.constants import TILE_CASTLE_BOTTOM
from foundry.smb3parse.levels import WORLD_COUNT
from foundry.smb3parse.levels.world_map import WorldMap
from foundry.smb3parse.levels.WorldMapPosition import WorldMapPosition


def test_get_castle_map_positions(rom_singleton: ROM):
    stock_castle_locations: list[WorldMapPosition] = [
        WorldMapPosition(1, 1, Point(12, 6)),
        WorldMapPosition(2, 2, Point(2, 4)),
        WorldMapPosition(3, 3, Point(9, 6)),
        WorldMapPosition(4, 1, Point(8, 4)),
        WorldMapPosition(5, 2, Point(2, 8)),
        WorldMapPosition(6, 3, Point(12, 4)),
        WorldMapPosition(7, 2, Point(8, 7)),
    ]

    found_castle_locations: list[WorldMapPosition | None] = []

    for world_number in range(1, WORLD_COUNT + 1):
        world: WorldMap = WorldMap.from_world_number(rom_singleton, world_number)

        for world_map_position in world.gen_positions():
            if world_map_position.tile() == TILE_CASTLE_BOTTOM:
                found_castle_locations.append(world_map_position)
                break
        else:
            found_castle_locations.append(None)

    for stock_location, found_location in zip(stock_castle_locations, found_castle_locations):
        assert found_location is not None
        assert found_location == stock_location, f"Failed at {found_location.world}"
