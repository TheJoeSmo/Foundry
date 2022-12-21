from foundry.game.File import ROM
from foundry.smb3parse.levels.world_map import get_all_world_maps
from foundry.smb3parse.levels.WorldMapPosition import WorldMapPosition


def find_world_position(rom: ROM, layout_address: int) -> WorldMapPosition | None:
    for world in get_all_world_maps(rom):
        for _level in world.gen_levels():
            if _level.layout_address == layout_address:
                return _level.world_map_position
    else:
        return None
