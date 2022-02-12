from enum import Enum


class DrawableType(str, Enum):
    """
    The type of drawable to be applied.
    """

    IMAGE_FROM_FILE = "FROM FILE"
    BLOCK_GROUP = "BLOCK GROUP"
    SPRITE_GROUP = "SPRITE GROUP"

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
