from functools import lru_cache

from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QImage, QPainter, Qt

from foundry.core.graphics_set.GraphicsSet import GraphicsSet
from foundry.core.palette import ColorPalette, PaletteGroup
from foundry.core.tiles import MASK_COLOR
from foundry.core.tiles.util import cached_tile_to_image
from foundry.game.File import ROM
from foundry.game.gfx.drawable import apply_selection_overlay
from foundry.game.gfx.drawable.Tile import Tile


@lru_cache(2**10)
def get_sprite(
    index: int,
    palette_group: PaletteGroup,
    palette_index: int,
    graphics_set: GraphicsSet,
    horizontal_mirror: bool = False,
    vertical_mirror: bool = False,
):
    if index > 0xFF:
        return Sprite(
            ROM().get_byte(index), palette_group, palette_index, graphics_set, horizontal_mirror, vertical_mirror
        )
    else:
        return Sprite(index, palette_group, palette_index, graphics_set, horizontal_mirror, vertical_mirror)


class Sprite:
    WIDTH: int = Tile.SIDE_LENGTH  # type: ignore
    HEIGHT: int = Tile.SIDE_LENGTH * 2  # type: ignore
    PIXEL_COUNT = WIDTH * HEIGHT

    _sprite_cache = {}

    def __init__(
        self,
        index: int,
        palette_group: PaletteGroup,
        palette_index: int,
        graphics_set: GraphicsSet,
        horizontal_mirror: bool = False,
        vertical_mirror: bool = False,
    ):
        self.index = index
        self.horizontal_mirror = horizontal_mirror
        self.vertical_mirror = vertical_mirror
        self.palette_group = palette_group
        self.palette_index = palette_index

        # can't hash list, so turn it into a string instead
        self._sprite_id = (index, str(palette_group), palette_index, graphics_set)

        self.top_tile = cached_tile_to_image(index, palette_group[palette_index], graphics_set)
        self.bottom_tile = cached_tile_to_image(index + 1, palette_group[palette_index], graphics_set)

        if vertical_mirror:
            self.top_tile, self.bottom_tile = self.bottom_tile, self.top_tile

        self.image = QImage(Sprite.WIDTH, Sprite.HEIGHT, QImage.Format.Format_RGB888)

        painter = QPainter(self.image)
        painter.drawImage(QPoint(0, 0), self.top_tile.copy().mirrored(horizontal_mirror, vertical_mirror))
        painter.drawImage(
            QPoint(0, Tile.HEIGHT),  # type: ignore
            self.bottom_tile.copy().mirrored(horizontal_mirror, vertical_mirror),
        )
        painter.end()

    def draw(self, painter: QPainter, x, y, width, height, selected=False, transparent=False):
        sprite_attributes = (
            self._sprite_id,
            self.horizontal_mirror,
            self.vertical_mirror,
            width,
            height,
            selected,
            transparent,
        )

        if sprite_attributes not in Sprite._sprite_cache:
            image = self.image.copy()

            if width != Sprite.WIDTH or height != Sprite.HEIGHT:
                image = image.scaled(width, height)

            # mask out the transparent pixels first
            mask = image.createMaskFromColor(QColor(*MASK_COLOR).rgb(), Qt.MaskMode.MaskOutColor)
            image.setAlphaChannel(mask)

            if not transparent:  # or self._whole_block_is_transparent:
                image = self._replace_transparent_with_background(image)

            if selected:
                apply_selection_overlay(image, mask)

            Sprite._sprite_cache[sprite_attributes] = image

        painter.drawImage(x, y, Sprite._sprite_cache[sprite_attributes])

    def _replace_transparent_with_background(self, image):
        # draw image on background layer, to fill transparent pixels
        background = image.copy()
        try:
            index = ColorPalette.from_default()[self.palette_group[self.palette_index, 0]].to_qt()
        except IndexError:
            return image
        background.fill(index)

        _painter = QPainter(background)
        _painter.drawImage(QPoint(), image)
        _painter.end()

        return background
