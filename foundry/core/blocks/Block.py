from collections.abc import Sequence

from attr import attrs

from foundry.core.geometry import Point
from foundry.core.namespace import (
    BoolValidator,
    ConcreteValidator,
    DefaultValidator,
    IntegerValidator,
    KeywordValidator,
    TupleValidator,
    default_validator,
    validate,
)

Pattern = tuple[int, int, int, int]


@attrs(slots=True, auto_attribs=True, eq=True, hash=True, frozen=True)
@default_validator
class Block(ConcreteValidator, KeywordValidator):
    """
    A representation of a Block inside the game.

    Attributes
    ----------
    point: Point
        The position of the block.
    patterns: Pattern
        The four tile indexes that define the graphics of block from the GraphicsSet.
    palette_index: int
        The palette index of the block into the PaletteGroup.
    do_not_render: bool
        If the block should not render.
    """

    __names__ = ("__Block_VALIDATOR__", "block", "Block", "BLOCK")
    __required_validators__ = (Point, TupleValidator, DefaultValidator, IntegerValidator, BoolValidator)

    point: Point
    patterns: Pattern
    palette_index: int
    do_not_render: bool = False

    @classmethod
    @validate(
        point=Point,
        pattern=DefaultValidator.generate_class(
            TupleValidator.generate_class((IntegerValidator, IntegerValidator, IntegerValidator, IntegerValidator)),
            (0, 0, 0, 0),
        ),
        palette_index=DefaultValidator.generate_class(IntegerValidator, 0),
        do_not_render=DefaultValidator.generate_class(BoolValidator, False),
    )
    def validate(cls, point: Point, pattern: Sequence[int], palette_index: int, do_not_render: bool):
        return cls(point, tuple(*pattern), palette_index, do_not_render)  # type: ignore
