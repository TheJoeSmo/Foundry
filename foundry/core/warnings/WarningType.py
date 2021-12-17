from enum import Enum


class WarningType(str, Enum):
    invalid_type = "INVALID OBJECT"
    invalid_position = "INVALID POSITION"
    invalid_size = "INVALID SIZE"
    invalid_extension_to_ground = "INVALID EXTENSION TO GROUND"
    outside_level_bounds = "OUTSIDE LEVEL BOUNDS"
    enemy_compatibility = "ENEMY COMPATIBILITY"
    invalid_warp = "INVALID WARP"

    @classmethod
    def has_value(cls, value: str) -> bool:
        """
        A convenience method to quickly determine if a value is a valid enumeration.

        Parameters
        ----------
        value : str
            The value to check against the enumeration.

        Returns
        -------
        bool
            If the value is inside the enumeration.
        """
        return value in cls._value2member_map_
