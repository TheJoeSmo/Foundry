from typing import Protocol

from attr import attrs
from PySide6.QtGui import QColor, QImage, QPainter

from foundry.core.Position import PositionProtocol
from foundry.core.Size import Size, SizeProtocol
from foundry.core.sprites import SPRITE_SIZE
from foundry.core.sprites.Sprite import SpriteProtocol
from foundry.game.gfx.drawable import MASK_COLOR
from foundry.game.gfx.drawable.Sprite import Sprite as MetaSprite
from foundry.game.gfx.GraphicsSet import GraphicsSetProtocol
from foundry.game.gfx.Palette import PaletteGroupProtocol


class SpriteGroupProtocol(Protocol):
    position: PositionProtocol
    sprites: list[SpriteProtocol]
    graphics_set: GraphicsSetProtocol
    palette_group: PaletteGroupProtocol

    @property
    def size(self) -> SizeProtocol:
        ...

    def image(self, scale_factor: int) -> QImage:
        ...


@attrs(slots=True, auto_attribs=True)
class SpriteGroup:
    """
    A representation of a group of sprites inside the game.

    Attributes
    ----------
    position: PositionProtocol
        The position of the sprite group.
    sprites: list[SpriteProtocol]
        The sprites that compose the sprite group.
    graphics_set: GraphicsSetProtocol
        The graphics to render the sprites with.
    palette_group: PaletteGroupProtocol
        The palettes to render the sprites with.
    """

    position: PositionProtocol
    sprites: list[SpriteProtocol]
    graphics_set: GraphicsSetProtocol
    palette_group: PaletteGroupProtocol

    @property
    def size(self) -> SizeProtocol:
        return Size(
            max([sprites.position.x for sprites in self.sprites]) + SPRITE_SIZE.width,
            max([sprites.position.y for sprites in self.sprites]) + SPRITE_SIZE.height,
        )

    def image(self, scale_factor: int = 1) -> QImage:
        image = QImage(self.size.width * scale_factor, self.size.height * scale_factor, QImage.Format_RGB888)
        image.fill(QColor(*MASK_COLOR))
        painter = QPainter(image)

        for sprite_data in self.sprites:
            if sprite_data.do_not_render:
                continue
            else:
                sprite = MetaSprite(
                    sprite_data.index,
                    tuple(tuple(c for c in pal) for pal in self.palette_group),  # type: ignore
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
