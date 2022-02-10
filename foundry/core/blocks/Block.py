from typing import Protocol, Type, TypeVar

from attr import attrs
from pydantic import BaseModel

from foundry.core.point.Point import (
    HashablePointProtocol,
    Point,
    PointProtocol,
    PydanticPoint,
)

Pattern = tuple[int, int, int, int]


class BlockProtocol(Protocol):
    point: PointProtocol
    patterns: Pattern
    palette_index: int
    do_not_render: bool


_T = TypeVar("_T", bound="Block")


@attrs(slots=True, auto_attribs=True, eq=True, hash=True, frozen=True)
class Block:
    """
    A representation of a Block inside the game.

    Attributes
    ----------
    point: HashablePointProtocol
        The position of the block.
    patterns: Pattern
        The four tile indexes that define the graphics of block from the GraphicsSetProtocol.
    palette_index: int
        The palette index of the block into the PaletteGroupProtocol.
    do_not_render: bool
        If the block should not render.
    """

    point: HashablePointProtocol
    patterns: Pattern
    palette_index: int
    do_not_render: bool = False

    @classmethod
    def from_values(
        cls: Type[_T], point: PointProtocol, patterns: Pattern, palette_index: int, do_not_render: bool = False
    ) -> _T:
        return cls(Point.from_point(point), patterns, palette_index, do_not_render)

    @classmethod
    def from_block(cls: Type[_T], block: BlockProtocol) -> _T:
        return cls.from_values(block.point, block.patterns, block.palette_index, block.do_not_render)


class PydanticBlock(BaseModel):
    point: PydanticPoint
    patterns: tuple[int, int, int, int] = (0, 0, 0, 0)
    palette_index: int = 0
    do_not_render: bool = False

    @property
    def block(self) -> BlockProtocol:
        return Block.from_values(self.point.point, self.patterns, self.palette_index, self.do_not_render)
