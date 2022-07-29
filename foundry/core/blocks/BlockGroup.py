from collections.abc import Sequence
from typing import Protocol, TypeVar

from attr import attrs
from PySide6.QtGui import QColor, QImage

from foundry.core.blocks import BLOCK_SIZE
from foundry.core.blocks.Block import Block, BlockProtocol, PydanticBlock
from foundry.core.blocks.util import block_to_image
from foundry.core.drawable.Drawable import Drawable
from foundry.core.geometry import Point, Size
from foundry.core.graphics_set.GraphicsSet import (
    GraphicsSetProtocol,
    PydanticGraphicsSet,
)
from foundry.core.painter.Painter import Painter
from foundry.core.palette.PaletteGroup import (
    HashablePaletteGroupProtocol,
    PaletteGroup,
    PaletteGroupProtocol,
    PydanticPaletteGroup,
)
from foundry.game.gfx.drawable import MASK_COLOR


class BlockGroupProtocol(Protocol):
    """
    A representation of a group of blocks inside the game.

    Attributes
    ----------
    position: Point
        The position of the block group.
    blocks: Sequence[BlockProtocol]
        The blocks that compose the block group.
    graphics_set: GraphicsSetProtocol
        The graphics to render the blocks with.
    palette_group: PaletteGroupProtocol
        The palettes to render the blocks with.
    """

    point: Point
    blocks: Sequence[BlockProtocol]
    graphics_set: GraphicsSetProtocol
    palette_group: PaletteGroupProtocol

    @property
    def size(self) -> Size:
        ...

    def image(self, scale_factor: int) -> QImage:
        ...


_T = TypeVar("_T", bound="BlockGroup")


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class BlockGroup:
    """
    A generic, hashable, representation of a group of blocks inside the game.

    Attributes
    ----------
    point: Point
        The point in space of the block group.
    blocks: tuple[BlockProtocol]
        The blocks that compose the block group.
    graphics_set: GraphicsSetProtocol
        The graphics to render the blocks with.
    palette_group: HashablePaletteGroupProtocol
        The palettes to render the blocks with.
    """

    point: Point
    blocks: tuple[BlockProtocol]
    graphics_set: GraphicsSetProtocol
    palette_group: HashablePaletteGroupProtocol

    @classmethod
    def from_values(
        cls: type[_T],
        point: Point,
        blocks: Sequence[BlockProtocol],
        graphics_set: GraphicsSetProtocol,
        palette_group: PaletteGroupProtocol,
    ) -> _T:
        """
        Generates a block group from any point, block, graphics set, and palette group, converting it to
        the correct hashable type if necessary.

        Parameters
        ----------
        point : Point
            The point in space of the block group.
        blocks : Sequence[BlockProtocol]
            The blocks that compose the block group.
        graphics_set : GraphicsSetProtocol
            The graphics to render the blocks with.
        palette_group : PaletteGroupProtocol
            The palettes to render the blocks with.
        """
        return cls(
            point,
            tuple(Block.from_block(block) for block in blocks),
            graphics_set,
            PaletteGroup.from_palette_group(palette_group),
        )

    @classmethod
    def from_block_group(cls: type[_T], block_group: BlockGroupProtocol) -> _T:
        """
        Generates this implementation of a block group from any other valid
        :class:`~foundry.core.blocks.BlockGroup.BlockGroupProtocol`, converting any types if necessary.

        Parameters
        ----------
        block_group : BlockGroupProtocol
            The initial block group to be converted from.
        """
        return cls.from_values(
            block_group.point, block_group.blocks, block_group.graphics_set, block_group.palette_group
        )

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


class PydanticBlockGroup(Drawable):
    point: Point
    blocks: list[PydanticBlock]
    graphics_set: PydanticGraphicsSet
    palette_group: PydanticPaletteGroup

    @property
    def block_group(self) -> BlockGroupProtocol:
        return BlockGroup.from_values(
            self.point,
            [b.block for b in self.blocks],
            self.graphics_set.graphics_set,
            self.palette_group.palette_group,
        )
