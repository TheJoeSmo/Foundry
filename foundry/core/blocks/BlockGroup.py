from collections.abc import Sequence

from attr import attrs
from PySide6.QtGui import QColor, QImage

from foundry.core.blocks import BLOCK_SIZE
from foundry.core.blocks.Block import Block
from foundry.core.blocks.util import block_to_image
from foundry.core.geometry import Point, Size
from foundry.core.graphics_set.GraphicsSet import GraphicsSet
from foundry.core.namespace import (
    ConcreteValidator,
    KeywordValidator,
    SequenceValidator,
    default_validator,
    validate,
)
from foundry.core.painter.Painter import Painter
from foundry.core.palette import PaletteGroup
from foundry.core.tiles import MASK_COLOR


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
@default_validator
class BlockGroup(ConcreteValidator, KeywordValidator):
    """
    A generic, hashable, representation of a group of blocks inside the game.

    Attributes
    ----------
    point: Point
        The point in space of the block group.
    blocks: tuple[Block]
        The blocks that compose the block group.
    graphics_set: GraphicsSet
        The graphics to render the blocks with.
    palette_group: PaletteGroup
        The palettes to render the blocks with.
    """

    __names__ = ("__BLOCK_GROUP_VALIDATOR__", "block group", "Block Group", "BLOCK GROUP")
    __required_validators__ = (SequenceValidator, Point, Block, GraphicsSet, PaletteGroup)

    point: Point
    blocks: tuple[Block]
    graphics_set: GraphicsSet
    palette_group: PaletteGroup

    @classmethod
    @validate(
        point=Point,
        blocks=SequenceValidator.generate_class(Block),
        graphics_set=GraphicsSet,
        palette_group=PaletteGroup,
    )
    def validate(cls, point: Point, blocks: Sequence[Block], graphics_set: GraphicsSet, palette_group: PaletteGroup):
        return cls(point, tuple(blocks), graphics_set, palette_group)

    @property
    def size(self) -> Size:
        """
        The maximum size required to render every block inside itself without any clipping.

        Returns
        -------
        Size
            Of the size required to render every block without clipping.
        """
        return Size(
            max(blocks.point.x for blocks in self.blocks) + BLOCK_SIZE.width,
            max(blocks.point.y for blocks in self.blocks) + BLOCK_SIZE.height,
        )

    def image(self, scale_factor: int = 1) -> QImage:
        """
        Generates an image of the respective blocks inside itself to the correct size and scale factor.

        Parameters
        ----------
        scale_factor : int, optional
            An integer multiple to expand the image by, by default 1.

        Returns
        -------
        QImage
            Of the block group and its respective blocks.
        """
        image = QImage(self.size.width * scale_factor, self.size.height * scale_factor, QImage.Format_RGB888)
        image.fill(QColor(*MASK_COLOR))

        with Painter(image) as p:
            for block in self.blocks:
                if block.do_not_render:
                    continue
                p.drawImage(
                    block.point.x,
                    block.point.y,
                    block_to_image(block, self.palette_group, self.graphics_set, scale_factor),
                )

        return image
