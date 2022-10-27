from typing import Protocol

from attr import attrs
from PySide6.QtGui import QColor, QImage, QPainter

from foundry.core.geometry import Point, Size
from foundry.core.graphics_set.GraphicsSet import GraphicsSet
from foundry.core.palette import PaletteGroup
from foundry.core.sprites import SPRITE_SIZE
from foundry.core.sprites.Sprite import SpriteProtocol
from foundry.core.tiles import MASK_COLOR
from foundry.game.gfx.drawable.Sprite import Sprite as MetaSprite


class SpriteGroupProtocol(Protocol):
    position: Point
    sprites: list[SpriteProtocol]
    graphics_set: GraphicsSet
    palette_group: PaletteGroup

    @property
    def size(self) -> Size:
        ...

    def image(self, scale_factor: int) -> QImage:
        ...


@attrs(slots=True, auto_attribs=True)
class SpriteGroup:
    """
    A representation of a group of sprites inside the game.

    Attributes
    ----------
    point: Point
        The point of the sprite group.
    sprites: list[SpriteProtocol]
        The sprites that compose the sprite group.
    graphics_set: GraphicsSet
        The graphics to render the sprites with.
    palette_group: PaletteGroup
        The palettes to render the sprites with.
    """

    position: Point
    sprites: list[SpriteProtocol]
    graphics_set: GraphicsSet
    palette_group: PaletteGroup

    @property
    def size(self) -> Size:
        return Size(
            max(sprites.position.x for sprites in self.sprites) + SPRITE_SIZE.width,
            max(sprites.position.y for sprites in self.sprites) + SPRITE_SIZE.height,
        )

    def image(self, scale_factor: int = 1) -> QImage:
        image = QImage(self.size.width * scale_factor, self.size.height * scale_factor, QImage.Format.Format_RGB888)
        image.fill(QColor(*MASK_COLOR))
        painter = QPainter(image)

        for sprite_data in self.sprites:
            if sprite_data.do_not_render:
                continue
            else:
                sprite = MetaSprite(
                    sprite_data.index,
                    self.palette_group,
                    sprite_data.palette_index,
                    self.graphics_set,
                    sprite_data.horizontal_mirror,
                    sprite_data.vertical_mirror,
                )
                sprite.draw(
                    painter,
                    sprite_data.position.x * scale_factor,
                    sprite_data.position.y * scale_factor,
                    SPRITE_SIZE.width * scale_factor,
                    SPRITE_SIZE.height * scale_factor,
                    transparent=True,
                )

        painter.end()
        return image
