from foundry.core.Enum import Enum


class WarningType(str, Enum):
    invalid_type = "INVALID OBJECT"
    invalid_position = "INVALID POSITION"
    invalid_size = "INVALID SIZE"
    invalid_extension_to_ground = "INVALID EXTENSION TO GROUND"
    outside_level_bounds = "OUTSIDE LEVEL BOUNDS"
    enemy_compatibility = "ENEMY COMPATIBILITY"
    invalid_warp = "INVALID WARP"
