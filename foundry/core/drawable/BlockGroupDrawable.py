from attr import attrs
from PySide6.QtGui import QImage

from foundry.core.blocks.BlockGroup import BlockGroupProtocol, PydanticBlockGroup
from foundry.core.drawable.Drawable import Drawable, DrawableProtocol
from foundry.core.geometry import Point, Size


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class BlockGroupDrawable:
    """
    A drawable block group.
    """

    point_offset: Point
    block_group: BlockGroupProtocol

    @property
    def size(self) -> Size:
        return self.block_group.size

    def image(self, scale_factor: int = 1) -> QImage:
        return self.block_group.image(scale_factor)


class PydanticBlockGroupDrawable(Drawable):
    block_group: PydanticBlockGroup

    @property
    def drawable(self) -> DrawableProtocol:
        return BlockGroupDrawable(self.point_offset.point, self.block_group.block_group)
