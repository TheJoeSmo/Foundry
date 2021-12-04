WORLD_MAP_OBJECT_SET = 0x00
PLAINS_OBJECT_SET = 0x01
DUNGEON_OBJECT_SET = 0x02
HILLY_OBJECT_SET = 0x03
SKY_OBJECT_SET = 0x04
PIRANHA_PLANT_OBJECT_SET = 0x05
WATER_OBJECT_SET = 0x06
MUSHROOM_OBJECT_SET = 0x07
PIPE_OBJECT_SET = 0x08
DESERT_OBJECT_SET = 0x09
AIR_SHIP_OBJECT_SET = 0x0A
GIANT_OBJECT_SET = 0x0B
ICE_OBJECT_SET = 0x0C
CLOUDY_OBJECT_SET = 0x0D
UNDERGROUND_OBJECT_SET = 0x0E
SPADE_BONUS_OBJECT_SET = 0x0F

PLAINS_GRAPHICS_SET = 0x01
DUNGEON_GRAPHICS_SET = 0x02
HILLY_GRAPHICS_SET = 0x03
SKY_GRAPHICS_SET = 0x04
DESERT_GRAPHICS_SET = 0x09
CLOUDY_GRAPHICS_SET = 0x0D
UNDERGROUND_GRAPHICS_SET = 0x0E
ENEMY_ITEM_GRAPHICS_SET = 0x4C

MIN_OBJECT_SET = WORLD_MAP_OBJECT_SET
MAX_OBJECT_SET = 0x0F

# amount of consecutive objects in a group, that share the same byte length
OBJECT_GROUP_SIZE = 16


def assert_valid_object_set_number(object_set_number: int):
    if not is_valid_object_set_number(object_set_number):
        raise ValueError(f"Object set number {object_set_number} is invalid.")


def is_valid_object_set_number(object_set_number: int):
    return object_set_number in range(MIN_OBJECT_SET, MAX_OBJECT_SET + 1)
