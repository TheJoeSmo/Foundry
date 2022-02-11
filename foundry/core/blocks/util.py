from functools import lru_cache

from attr import attrs
from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QImage

from foundry.core.blocks import BLOCK_SIZE, PATTERN_LOCATIONS
from foundry.core.blocks.Block import Block, BlockProtocol, Pattern
from foundry.core.graphics_set.GraphicsSet import GraphicsSetProtocol
from foundry.core.painter.Painter import Painter
from foundry.core.palette.PaletteGroup import (
    HashablePaletteGroupProtocol,
    PaletteGroup,
    PaletteGroupProtocol,
)
from foundry.game.gfx.drawable import MASK_COLOR
from foundry.game.gfx.drawable.Tile import Tile


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class _Block:
    """
    A representation of a Block inside the game.

    Attributes
    ----------
    pattern: Pattern
        The four tile indexes that define the graphics of block from the GraphicsSetProtocol.
    palette_index: int
        The palette index of the block into the palette group.
    palette_group: HashablePaletteGroupProtocol
        The a hashable palette group.
    graphics_set: GraphicsSetProtocol
        The base of all images generated for the Block.
    do_not_render: bool
        If the sprite should not render.
    """

    patterns: Pattern
    palette_index: int
    palette_group: HashablePaletteGroupProtocol
    graphics_set: GraphicsSetProtocol
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
    image = QImage(BLOCK_SIZE.width, BLOCK_SIZE.height, QImage.Format_RGB888)
    image.fill(QColor(*MASK_COLOR))
    patterns = [Tile(index, block.palette_group, block.palette_index, block.graphics_set) for index in block.patterns]
    with Painter(image) as p:
        for (pattern, position) in zip(patterns, PATTERN_LOCATIONS):
            p.drawImage(QPoint(position.x, position.y), pattern.as_image())
    return image.scaled(scale_factor, scale_factor)


@lru_cache(2 ** 10)
def cached_block_to_image(
    block: Block, palette_group: HashablePaletteGroupProtocol, graphics_set: GraphicsSetProtocol, scale_factor: int = 1
) -> QImage:
    """
    Generates and caches a NES block with a given palette and graphics as a QImage.

    Parameters
    ----------
    block : Block
        The block data to be rendered to the image.
    palette_group : HashablePaletteGroupProtocol
        The specific palette to use for the block.
    graphics_set : GraphicsSetProtocol
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


def block_to_image(
    block: BlockProtocol, palette_group: PaletteGroupProtocol, graphics_set: GraphicsSetProtocol, scale_factor: int = 1
) -> QImage:
    """
    Generates a block with a given palette and graphics as a QImage.

    Parameters
    ----------
    block : BlockProtocol
        The block data to be rendered to the image.
    palette_group : PaletteGroupProtocol
        The specific palette to use for the block.
    graphics_set : GraphicsSetProtocol
        The specific graphics to use for the block.
    scale_factor : int, optional
        The multiple of 16 that the image will be created as, by default 1

    Returns
    -------
    QImage
        That represents the block.
    """
    return cached_block_to_image(
        Block.from_block(block), PaletteGroup.from_palette_group(palette_group), graphics_set, scale_factor
    )
