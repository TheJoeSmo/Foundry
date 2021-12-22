from typing import Protocol

from attr import attrs

from foundry.core.Position import PositionProtocol


class SpriteProtocol(Protocol):
    position: PositionProtocol
    index: int
    palette_index: int
    horizontal_mirror: bool
    vertical_mirror: bool
    do_not_render: bool


@attrs(slots=True, auto_attribs=True)
class Sprite:
    """
    A representation of a Sprite inside the game.

    Attributes
    ----------
    position: PositionProtocol
        The position of the sprite.
    index: int
        The index into the graphics set of the sprite.
    palette_index: int
        The palette index of the sprite into the PaletteGroupProtocol.
    horizontal_mirror: bool
        If the sprite should be horizontally flipped.
    vertical_mirror: bool
        If the sprite should be vertically flipped.
    do_not_render: bool
        If the sprite should not render.
    """

    position: PositionProtocol
    index: int
    palette_index: int
    horizontal_mirror: bool = False
    vertical_mirror: bool = False
    do_not_render: bool = False
