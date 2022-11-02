from collections.abc import Sequence
from functools import lru_cache

from attr import attrs
from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QImage

from foundry.core.geometry import Point, Size
from foundry.core.graphics_set.GraphicsSet import GraphicsSet
from foundry.core.namespace import (
    BoolValidator,
    ConcreteValidator,
    DefaultValidator,
    IntegerValidator,
    KeywordValidator,
    SequenceValidator,
    TupleValidator,
    default_validator,
    validate,
)
from foundry.core.painter.Painter import Painter
from foundry.core.palette import PaletteGroup
from foundry.core.tiles import MASK_COLOR, tile_to_image

BLOCK_SIZE: Size = Size(16, 16)
PATTERN_LOCATIONS: tuple[Point, Point, Point, Point] = (
    Point(0, 0),
    Point(8, 0),
    Point(0, 8),
    Point(8, 8),
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
        image = QImage(self.size.width * scale_factor, self.size.height * scale_factor, QImage.Format.Format_RGB888)
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


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class _Block:
    """
    A representation of a Block inside the game.

    Attributes
    ----------
    pattern: Pattern
        The four tile indexes that define the graphics of block from the GraphicsSet.
    palette_index: int
        The palette index of the block into the palette group.
    palette_group: PaletteGroup
        The a hashable palette group.
    graphics_set: GraphicsSet
        The base of all images generated for the Block.
    do_not_render: bool
        If the sprite should not render.
    """

    patterns: Pattern
    palette_index: int
    palette_group: PaletteGroup
    graphics_set: GraphicsSet
    do_not_render: bool = False


def _block_to_image(block: _Block, scale_factor: int = 1) -> QImage:
    """
    Generates a QImage of a block from the NES.

    Parameters
    ----------
    block : _Block
        The dataclass instance that represents a block inside the game.
    scale_factor : int, optional
        The multiple of 16 that the image will be created as, by default 1.

    Returns
    -------
    QImage
        That represents the block.
    """
    image = QImage(BLOCK_SIZE.width, BLOCK_SIZE.height, QImage.Format.Format_RGB888)
    image.fill(QColor(*MASK_COLOR))
    patterns = [
        tile_to_image(index, block.palette_group[block.palette_index], block.graphics_set) for index in block.patterns
    ]
    with Painter(image) as p:
        for (pattern, point) in zip(patterns, PATTERN_LOCATIONS):
            p.drawImage(QPoint(point.x, point.y), pattern)
    return image.scaled(scale_factor, scale_factor)


@lru_cache(2**10)
def block_to_image(
    block: Block, palette_group: PaletteGroup, graphics_set: GraphicsSet, scale_factor: int = 1
) -> QImage:
    """
    Generates and caches a NES block with a given palette and graphics as a QImage.

    Parameters
    ----------
    block : Block
        The block data to be rendered to the image.
    palette_group : PaletteGroup
        The specific palette to use for the block.
    graphics_set : GraphicsSet
        The specific graphics to use for the block.
    scale_factor : int, optional
        The multiple of 16 that the image will be created as, by default 1

    Returns
    -------
    QImage
        That represents the block.

    Notes
    -----
    Since this method is being cached, it is expected that every parameter is hashable and immutable.  If this does not
    occur, there is a high chance of an errors to linger throughout the program.
    """
    return _block_to_image(
        _Block(block.patterns, block.palette_index, palette_group, graphics_set, block.do_not_render), scale_factor
    )
