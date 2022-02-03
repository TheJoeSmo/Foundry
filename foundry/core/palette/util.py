from functools import cache

from foundry.core.palette import (
    PALETTE_BASE_ADDRESS,
    PALETTE_OFFSET_LIST,
    PALETTE_OFFSET_SIZE,
)
from foundry.game.File import ROM


@cache
def get_internal_palette_offset(tileset: int) -> int:
    """
    Provides the absolute internal point of the palette group offset from ROM.

    Parameters
    ----------
    tileset : int
        The tileset to find the absolute internal point of.

    Returns
    -------
    int
        The absolute internal point of the tileset's palette group.
    """
    return PALETTE_BASE_ADDRESS + ROM().little_endian(PALETTE_OFFSET_LIST + (tileset * PALETTE_OFFSET_SIZE))
