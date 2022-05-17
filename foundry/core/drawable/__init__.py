from foundry.core.Enum import Enum


class DrawableType(str, Enum):
    """
    The type of drawable to be applied.
    """

    IMAGE_FROM_FILE = "FROM FILE"
    BLOCK_GROUP = "BLOCK GROUP"
    SPRITE_GROUP = "SPRITE GROUP"
