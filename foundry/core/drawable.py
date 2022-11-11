from collections.abc import Generator, Sequence
from functools import cache, lru_cache
from pathlib import Path
from typing import ClassVar

from attr import attrs
from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QImage, QPainter, Qt

from foundry.core.file import FilePath
from foundry.core.geometry import Point, Rect, Size
from foundry.core.graphics_set.GraphicsSet import GraphicsSet
from foundry.core.namespace import (
    BoolValidator,
    ConcreteValidator,
    DefaultValidator,
    IntegerValidator,
    KeywordValidator,
    OptionalValidator,
    SequenceValidator,
    TupleValidator,
    TypeInformation,
    custom_validator,
    default_validator,
    validate,
)
from foundry.core.painter.Painter import Painter
from foundry.core.palette import Color, Palette, PaletteGroup

PIXELS: int = 64
BYTES_PER_TILE: int = 16
TILE_SIZE: Size = Size(8, 8)
BLOCK_SIZE: Size = Size(16, 16)
SPRITE_SIZE: Size = Size(8, 16)
PATTERN_LOCATIONS: tuple[Point, Point, Point, Point] = (
    Point(0, 0),
    Point(8, 0),
    Point(0, 8),
    Point(8, 8),
)
MASK_COLOR = Color(0xFF, 0x33, 0xFF)
SELECTION_OVERLAY_COLOR = QColor(20, 87, 159, 80)
PIXEL_OFFSET = 8

Pattern = tuple[int, int, int, int]


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class _Tile:
    """
    A representation of a tile inside the game.

    Attributes
    ----------
    index: int
        The tile index that define the graphics from the GraphicsSet.
    palette: Palette
        The palette.
    graphics_set: GraphicsSet
        The base of all images generated for the tile.
    use_background_color: bool, optional
        If the natural background color should be used or if a mask color should be applied.
    """

    index: int
    palette: Palette
    graphics_set: GraphicsSet
    use_background_color: bool = False

    @cache
    def __bytes__(self) -> bytes:
        return bytes(self.graphics_set)[self.index * BYTES_PER_TILE : (self.index + 1) * BYTES_PER_TILE]

    @property
    def pixels_indexes(self) -> Generator[int, None, None]:
        """
        Provides a generator that generates the pixels in order from top to bottom of the tile.

        Yields
        -------
        Generator[int, None, None]
            A generator of pixels from top to bottom in 2BPP format.
        """
        for i in range(PIXELS):
            byte_index = i // TILE_SIZE.height
            bit_index = 2 ** (7 - (i % TILE_SIZE.width))

            yield (int(bool(bytes(self)[PIXEL_OFFSET + byte_index] & bit_index)) << 1) | int(
                bool(bytes(self)[byte_index] & bit_index)
            )

    @property
    def pixels(self) -> bytes:
        """
        Generates a series of bytes in RGB color format that represents the tile.

        Returns
        -------
        bytes
            That represent an RGB tile image.
        """
        pixels = bytearray()
        assert isinstance(self.palette, Palette)

        for pixel_index in self.pixels_indexes:
            if not self.use_background_color and pixel_index == 0:
                pixels.extend(MASK_COLOR.to_rgb_bytes())
            else:
                pixels.extend(self.palette[pixel_index, Color].to_rgb_bytes())

        return bytes(pixels)


def _tile_to_image(tile: _Tile, scale_factor: int = 1) -> QImage:
    """
    Generates a QImage of a tile from the NES.

    Parameters
    ----------
    tile : _Tile
        The dataclass instance that represents a tile inside the game.
    scale_factor : int, optional
        The multiple of 8 that the image will be created as, by default 1.

    Returns
    -------
    QImage
        That represents the tile.
    """
    image = QImage(tile.pixels, TILE_SIZE.width, TILE_SIZE.height, QImage.Format.Format_RGB888)
    return image.scaled(TILE_SIZE.width * scale_factor, TILE_SIZE.height * scale_factor)


@lru_cache(2**10)
def _cached_tile_to_image(
    tile_index: int,
    palette: Palette,
    graphics_set: GraphicsSet,
    scale_factor: int = 1,
    use_background_color: bool = False,
) -> QImage:
    return _tile_to_image(_Tile(tile_index, palette, graphics_set, use_background_color), scale_factor)


def tile_to_image(
    tile_index: int,
    palette: Palette,
    graphics_set: GraphicsSet,
    scale_factor: int = 1,
    use_background_color: bool = False,
) -> QImage:
    """
    Generates and caches a NES tile with a given palette and graphics as a QImage.

    Parameters
    ----------
    tile_index: int
        The tile index into the graphics set.
    palette : Palette
        The specific palette to use for the tile.
    graphics_set : GraphicsSet
        The specific graphics to use for the tile.
    scale_factor : int, optional
        The multiple of 8 that the image will be created as, by default 1
    use_background_color: bool, optional
        If the natural background color should be used or if a mask color should be applied.

    Returns
    -------
    QImage
        That represents the tile.

    Notes
    -----
    Since this method is being cached, it is expected that every parameter is hashable and immutable.  If this does not
    occur, there is a high chance of an errors to linger throughout the program.
    """
    return _cached_tile_to_image(tile_index, palette, graphics_set, scale_factor, use_background_color)


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
    index: int | None = None
    size: ClassVar[Size] = BLOCK_SIZE

    @classmethod
    def from_tsa(cls, point: Point, index: int, tsa: bytes, do_not_render: bool = False):
        block = cls(
            point,
            (tsa[index], tsa[index + 512], tsa[index + 256], tsa[index + 768]),
            index // 0x40,
            do_not_render,
            index,
        )
        return block

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


def _block_to_image(block: _Block, scale_factor: int = 1, use_background_color: bool = False) -> QImage:
    """
    Generates a QImage of a block from the NES.

    Parameters
    ----------
    block : _Block
        The dataclass instance that represents a block inside the game.
    scale_factor : int, optional
        The multiple of 16 that the image will be created as, by default 1.
    use_background_color: bool, optional
        If the natural background color should be used or if a mask color should be applied.

    Returns
    -------
    QImage
        That represents the block.
    """
    image = QImage(BLOCK_SIZE.width, BLOCK_SIZE.height, QImage.Format.Format_RGB888)
    if use_background_color:
        image.fill(block.palette_group.background_color)
    else:
        image.fill(MASK_COLOR.to_qt())
    patterns = [
        tile_to_image(
            index,
            block.palette_group[block.palette_index],
            block.graphics_set,
            use_background_color=use_background_color,
        )
        for index in block.patterns
    ]
    with Painter(image) as p:
        for (pattern, point) in zip(patterns, PATTERN_LOCATIONS):
            p.drawImage(QPoint(point.x, point.y), pattern)
    return image.scaled(scale_factor, scale_factor)


@lru_cache(2**10)
def _cached_block_to_image(
    block: Block,
    palette_group: PaletteGroup,
    graphics_set: GraphicsSet,
    scale_factor: int = 1,
    use_background_color: bool = False,
) -> QImage:
    return _block_to_image(
        _Block(block.patterns, block.palette_index, palette_group, graphics_set, block.do_not_render),
        scale_factor,
        use_background_color,
    )


def block_to_image(
    block: Block,
    palette_group: PaletteGroup,
    graphics_set: GraphicsSet,
    scale_factor: int = 1,
    use_background_color: bool = False,
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
    use_background_color: bool, optional
        If the natural background color should be used or if a mask color should be applied.

    Returns
    -------
    QImage
        That represents the block.

    Notes
    -----
    Since this method is being cached, it is expected that every parameter is hashable and immutable.  If this does not
    occur, there is a high chance of an errors to linger throughout the program.
    """
    return _cached_block_to_image(block, palette_group, graphics_set, scale_factor, use_background_color)


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class Sprite:
    """
    A representation of a Sprite inside the game.

    Attributes
    ----------
    point: Point
        The point of the sprite.
    index: int
        The index into the graphics set of the sprite.
    palette_index: int
        The palette index of the sprite into the PaletteGroup.
    horizontal_mirror: bool
        If the sprite should be horizontally flipped.
    vertical_mirror: bool
        If the sprite should be vertically flipped.
    do_not_render: bool
        If the sprite should not render.
    """

    point: Point
    index: int
    palette_index: int
    horizontal_mirror: bool = False
    vertical_mirror: bool = False
    do_not_render: bool = False


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class SpriteGroup:
    """
    A representation of a group of sprites inside the game.

    Attributes
    ----------
    point: Point
        The point of the sprite group.
    sprites: tuple[Sprite, ...]
        The sprites that compose the sprite group.
    graphics_set: GraphicsSet
        The graphics to render the sprites with.
    palette_group: PaletteGroup
        The palettes to render the sprites with.
    """

    point: Point
    sprites: tuple[Sprite, ...]
    graphics_set: GraphicsSet
    palette_group: PaletteGroup

    @property
    def size(self) -> Size:
        return Size(
            max(sprites.point.x for sprites in self.sprites) + SPRITE_SIZE.width,
            max(sprites.point.y for sprites in self.sprites) + SPRITE_SIZE.height,
        )

    def image(self, scale_factor: int = 1) -> QImage:
        image = QImage(self.size.width * scale_factor, self.size.height * scale_factor, QImage.Format.Format_RGB888)
        image.fill(QColor(*MASK_COLOR))

        with Painter(image) as p:
            for sprite in self.sprites:
                if sprite.do_not_render:
                    continue
                p.drawImage(
                    sprite.point.x * scale_factor,
                    sprite.point.y * scale_factor,
                    sprite_to_image(sprite, self.palette_group, self.graphics_set, scale_factor),
                )

        return image


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class _Sprite:
    """
    A representation of a Sprite inside the game.

    Attributes
    ----------
    index: int
        The index into the graphics set of the sprite.
    palette_index: int
        The palette index of the sprite into the palette group.
    palette_group: PaletteGroup
        The a hashable palette group.
    graphics_set: GraphicsSet
        The base of all images generated for the Sprite.
    horizontal_mirror: bool
        If the sprite should be horizontally flipped.
    vertical_mirror: bool
        If the sprite should be vertically flipped.
    do_not_render: bool
        If the sprite should not render.
    """

    index: int
    palette_index: int
    palette_group: PaletteGroup
    graphics_set: GraphicsSet
    horizontal_mirror: bool = False
    vertical_mirror: bool = False
    do_not_render: bool = False


def _sprite_to_image(sprite: _Sprite, scale_factor: int = 1) -> QImage:
    """
    Generates a QImage of a sprite from the NES.

    Parameters
    ----------
    sprite : _Sprite
        The dataclass instance that represents a sprite inside the game.
    scale_factor : int, optional
        The multiple of 16 that the image will be created as, by default 1.

    Returns
    -------
    QImage
        That represents the sprite.
    """
    image: QImage = QImage(SPRITE_SIZE.width, SPRITE_SIZE.height, QImage.Format.Format_RGB888)
    image.fill(QColor(*MASK_COLOR))

    top_tile: QImage = tile_to_image(sprite.index, sprite.palette_group[sprite.palette_index], sprite.graphics_set)
    bottom_tile: QImage = tile_to_image(
        sprite.index + 1, sprite.palette_group[sprite.palette_index], sprite.graphics_set
    )

    if sprite.vertical_mirror:
        top_tile, bottom_tile = bottom_tile, top_tile

    with Painter(image) as p:
        p.drawImage(QPoint(0, 0), top_tile.copy().mirrored(sprite.horizontal_mirror, sprite.vertical_mirror))
        p.drawImage(
            QPoint(0, TILE_SIZE.height),
            bottom_tile.copy().mirrored(sprite.horizontal_mirror, sprite.vertical_mirror),
        )

    return image.scaled(scale_factor * SPRITE_SIZE.width, scale_factor * SPRITE_SIZE.height)


@lru_cache(2**10)
def _cached_sprite_to_image(
    sprite: Sprite, palette_group: PaletteGroup, graphics_set: GraphicsSet, scale_factor: int = 1
) -> QImage:
    return _sprite_to_image(
        _Sprite(
            sprite.index,
            sprite.palette_index,
            palette_group,
            graphics_set,
            sprite.horizontal_mirror,
            sprite.vertical_mirror,
            sprite.do_not_render,
        ),
        scale_factor,
    )


def sprite_to_image(
    sprite: Sprite, palette_group: PaletteGroup, graphics_set: GraphicsSet, scale_factor: int = 1
) -> QImage:
    """
    Generates and caches a NES sprite with a given palette and graphics as a QImage.

    Parameters
    ----------
    sprite : Sprite
        The sprite data to be rendered to the image.
    palette_group : PaletteGroup
        The specific palette to use for the sprite.
    graphics_set : GraphicsSet
        The specific graphics to use for the sprite.
    scale_factor : int, optional
        The multiple of 16 that the image will be created as, by default 1

    Returns
    -------
    QImage
        That represents the sprite.

    Notes
    -----
    Since this method is being cached, it is expected that every parameter is hashable and immutable.  If this does not
    occur, there is a high chance of an errors to linger throughout the program.
    """
    return _cached_sprite_to_image(sprite, palette_group, graphics_set, scale_factor)


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
@custom_validator("BLOCK GROUP", method_name="validate_from_block_group")
@custom_validator("FROM FILE", method_name="validate_from_file")
class Drawable(ConcreteValidator, KeywordValidator):
    __names__ = ("__DRAWABLE_VALIDATOR__", "drawable", "Drawable", "DRAWABLE")
    __required_validators__ = (OptionalValidator, DefaultValidator, FilePath, Point, Rect, BlockGroup)
    __type_default__ = TypeInformation("FROM FILE")

    base_image: QImage
    point_offset: Point = Point(0, 0)

    @property
    def size(self) -> Size:
        return Size.from_qt(self.base_image.size())

    def image(self, scale_factor: int = 1) -> QImage:
        return self.base_image.scaled((self.size * scale_factor).to_qt())

    @classmethod
    def from_block_group(cls, block_group: BlockGroup, point_offset: Point = Point(0, 0)):
        return cls(block_group.image(), point_offset)

    @classmethod
    @validate(block_group=BlockGroup, point_offset=DefaultValidator.generate_class(Point, Point(0, 0)))
    def validate_from_block_group(cls, block_group: BlockGroup, point_offset: Point):
        return cls.from_block_group(block_group, point_offset)

    @classmethod
    def from_image(
        cls,
        image: QImage,
        image_offset: Rect | None = None,
        use_transparency: bool = True,
        point_offset: Point = Point(0, 0),
    ):
        assert use_transparency
        image = image if image_offset is None else image.copy(image_offset.to_qt())
        if use_transparency:
            mask: QImage = image.createMaskFromColor(QColor(*MASK_COLOR).rgb(), Qt.MaskMode.MaskOutColor)
            image.setAlphaChannel(mask)
        return cls(image, point_offset)

    @classmethod
    def from_file(
        cls,
        path: Path,
        image_offset: Rect | None = None,
        use_transparency: bool = True,
        point_offset: Point = Point(0, 0),
    ):
        return cls.from_image(QImage(path), image_offset, use_transparency, point_offset)

    @classmethod
    @validate(
        path=FilePath,
        image_offset=OptionalValidator.generate_class(Rect),
        use_transparency=DefaultValidator.generate_class(BoolValidator, True),
        point_offset=DefaultValidator.generate_class(Point, Point(0, 0)),
    )
    def validate_from_file(cls, path: FilePath, image_offset: Rect | None, use_transparency: bool, point_offset: Point):
        return cls.from_file(path, image_offset, use_transparency, point_offset)


def apply_selection_overlay(image: QImage, mask: QImage):
    overlay = image.copy()
    overlay.fill(SELECTION_OVERLAY_COLOR)
    overlay.setAlphaChannel(mask)

    _painter = QPainter(image)
    _painter.drawImage(QPoint(), overlay)
    _painter.end()
