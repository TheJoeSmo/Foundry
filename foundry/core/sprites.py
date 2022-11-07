from functools import lru_cache

from attr import attrs
from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QImage

from foundry.core.geometry import Point, Size
from foundry.core.graphics_set.GraphicsSet import GraphicsSet
from foundry.core.painter.Painter import Painter
from foundry.core.palette import PaletteGroup
from foundry.core.tiles import MASK_COLOR, TILE_SIZE, tile_to_image

SPRITE_SIZE: Size = Size(8, 16)


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

    return image.scaled(scale_factor, scale_factor)


@lru_cache(2**10)
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
        That represents the block.

    Notes
    -----
    Since this method is being cached, it is expected that every parameter is hashable and immutable.  If this does not
    occur, there is a high chance of an errors to linger throughout the program.
    """
    return _sprite_to_image(
        _Sprite(
            sprite.index,
            sprite.palette_index,
            palette_group,
            graphics_set,
            sprite.horizontal_mirror,
            sprite.vertical_mirror,
            sprite.do_not_render,
        )
    )
