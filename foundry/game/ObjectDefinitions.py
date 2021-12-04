from enum import Enum
from json import loads

from pydantic import BaseModel

from foundry import tileset_definitions
from foundry.smb3parse.objects.object_set import (
    AIR_SHIP_OBJECT_SET,
    CLOUDY_OBJECT_SET,
    DESERT_OBJECT_SET,
    DUNGEON_OBJECT_SET,
    GIANT_OBJECT_SET,
    HILLY_OBJECT_SET,
    ICE_OBJECT_SET,
    MUSHROOM_OBJECT_SET,
    PIPE_OBJECT_SET,
    PIRANHA_PLANT_OBJECT_SET,
    PLAINS_OBJECT_SET,
    SKY_OBJECT_SET,
    SPADE_BONUS_OBJECT_SET,
    UNDERGROUND_OBJECT_SET,
    WATER_OBJECT_SET,
    WORLD_MAP_OBJECT_SET,
)


class GeneratorType(int, Enum):
    """
    Level objects are generated using different methods, depending on their generator type. Some objects extend until
    they hit another object, some extend up to the sky. To identify in what way a specific type of level object is
    constructed, this enum lists the known generator types.
    """

    HORIZONTAL = 0
    VERTICAL = 1  # vertical downward
    DIAG_DOWN_LEFT = 2
    DESERT_PIPE_BOX = 3
    DIAG_DOWN_RIGHT = 4
    DIAG_UP_RIGHT = 5
    HORIZ_TO_GROUND = 6
    HORIZONTAL_2 = 7  # special case of horizontal, floating boxes, ceilings
    DIAG_WEIRD = 8  #
    SINGLE_BLOCK_OBJECT = 9
    CENTERED = 10  # like spinning platforms
    PYRAMID_TO_GROUND = 11  # to the ground or next object
    PYRAMID_2 = 12  # doesn't exist?
    TO_THE_SKY = 13
    ENDING = 14


class EndType(int, Enum):
    """
    Some level objects have blocks designated to be used at their ends. For example pipes, which can be extended, but
    always end at one side with the same couple of blocks. To keep track of where those special blocks are to be placed,
    this enum is used. When the value is TWO_ENDS they are always on opposite sides and whether they are left and right
    or top and bottom depends on the generator type of the object.
    """

    UNIFORM = 0
    END_ON_TOP_OR_LEFT = 1
    END_ON_BOTTOM_OR_RIGHT = 2
    TWO_ENDS = 3


class TilesetDefinition(BaseModel):
    domain: int
    min_value: int
    max_value: int
    bmp_width: int
    bmp_height: int
    blocks: list[int]
    orientation: GeneratorType
    ending: EndType
    size: int = 3
    description: str

    @property
    def object_design_length(self) -> int:
        return len(self.blocks)

    @property
    def is_4byte(self) -> bool:
        return self.size == 4

    class Config:
        use_enum_values = True


class Tileset(BaseModel):
    __root__: list[TilesetDefinition]


class Tilesets(BaseModel):
    __root__: list[Tileset]


with open(tileset_definitions, "r") as f:
    object_metadata = Tilesets(__root__=loads(f.read()))


object_set_to_definition = {
    WORLD_MAP_OBJECT_SET: 0,
    PLAINS_OBJECT_SET: 1,
    MUSHROOM_OBJECT_SET: 1,
    SPADE_BONUS_OBJECT_SET: 1,
    HILLY_OBJECT_SET: 2,
    SKY_OBJECT_SET: 3,
    DUNGEON_OBJECT_SET: 4,
    AIR_SHIP_OBJECT_SET: 5,
    CLOUDY_OBJECT_SET: 6,
    DESERT_OBJECT_SET: 7,
    WATER_OBJECT_SET: 8,
    PIPE_OBJECT_SET: 8,
    PIRANHA_PLANT_OBJECT_SET: 9,
    GIANT_OBJECT_SET: 9,
    ICE_OBJECT_SET: 10,
    UNDERGROUND_OBJECT_SET: 11,
}
