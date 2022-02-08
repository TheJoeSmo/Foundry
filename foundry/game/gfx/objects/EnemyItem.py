from PySide6.QtCore import QRect, QSize
from PySide6.QtGui import QColor, QImage, QPainter, Qt

from foundry.core.graphics_page.GraphicsPage import GraphicsPage
from foundry.core.graphics_set.GraphicsSet import GraphicsSet, GraphicsSetProtocol
from foundry.core.palette.PaletteGroup import MutablePaletteGroup
from foundry.core.point.Point import MutablePoint, PointProtocol
from foundry.game.EnemyDefinitions import (
    EnemyDefinition,
    GeneratorType,
    get_enemy_metadata,
)
from foundry.game.gfx.drawable import apply_selection_overlay
from foundry.game.gfx.drawable.Block import Block
from foundry.game.gfx.drawable.Sprite import get_sprite
from foundry.game.gfx.objects.Enemy import Enemy
from foundry.game.gfx.objects.ObjectLike import ObjectLike

MASK_COLOR = [0xFF, 0x33, 0xFF]


class EnemyObject(ObjectLike):
    def __init__(self, data, png_data, palette_group: MutablePaletteGroup):
        super().__init__()
        self.enemy = Enemy.from_bytes(data)

        self.palette_group = tuple(tuple(c for c in pal) for pal in palette_group)

        self.png_data = png_data

        self.selected = False

        self._render()

    @property
    def definition(self) -> EnemyDefinition:
        return get_enemy_metadata().__root__[self.obj_index]

    @property
    def rect(self):
        bmp_width = (
            self.definition.bmp_width
            if not GeneratorType.SINGLE_SPRITE_OBJECT == self.definition.orientation
            else self.definition.bmp_width // 2
        )
        width = self.definition.rect_width if self.definition.rect_width != 0 else bmp_width
        height = self.definition.rect_height if self.definition.rect_height != 0 else self.definition.bmp_height

        return QRect(
            self.position.x - self.definition.rect_x_offset,
            self.position.y - self.definition.rect_y_offset,
            width,
            height,
        )

    @property
    def graphics_set(self) -> GraphicsSetProtocol:
        if GeneratorType.SINGLE_SPRITE_OBJECT == self.definition.orientation:
            return GraphicsSet(tuple(GraphicsPage(page) for page in self.definition.pages))
        else:
            raise NotImplementedError

    @property
    def name(self) -> str:
        return self.definition.description

    @property
    def width(self) -> int:
        return self.definition.bmp_width

    @property
    def height(self) -> int:
        return self.definition.bmp_height

    def _render(self):
        if not GeneratorType.SINGLE_SPRITE_OBJECT == self.definition.orientation:
            self._render_blocks()
        else:
            self._render_sprites()

    def _render_sprites(self):
        self.sprites = self.definition.sprites

    def _render_blocks(self):
        self.blocks = []

        block_ids = self.definition.blocks

        for block_id in block_ids:
            x = (block_id % 64) * Block.WIDTH
            y = (block_id // 64) * Block.WIDTH

            self.blocks.append(self.png_data.copy(QRect(x, y, Block.WIDTH, Block.HEIGHT)))

    def render(self):
        # nothing to re-render since enemies are just copied over
        pass

    def draw(self, painter: QPainter, block_length, transparency, *, is_icon=False):
        if not GeneratorType.SINGLE_SPRITE_OBJECT == self.definition.orientation:
            self.draw_blocks(painter, block_length, is_icon)
        else:
            self.draw_sprites(painter, block_length // 2, transparency, is_icon)

    def draw_sprites(self, painter: QPainter, scale_factor, transparency, is_icon):
        for i, sprite_info in enumerate(self.sprites):
            if sprite_info.index < 0:
                continue

            x = (self.position.x * 2) + (i % self.width) if not is_icon else (i % self.width)
            y = self.position.y + (i // self.width) if not is_icon else (i // self.width)
            x += sprite_info.x_offset / 16
            y -= sprite_info.y_offset / 16

            if is_icon:
                definition = get_enemy_metadata().__root__[self.obj_index]
                x_offset, y_offset = definition.suggested_icon_x_offset, definition.suggested_icon_y_offset
                x += x_offset / 16
                y -= y_offset / 16
            if not is_icon:
                y_offset = self.height - 1
                y -= y_offset

            sprite = get_sprite(
                sprite_info.index,
                self.palette_group,
                sprite_info.palette_index,
                self.graphics_set,
                sprite_info.horizontal_mirror,
                sprite_info.vertical_mirror,
            )
            sprite.draw(
                painter,
                x * scale_factor,
                y * scale_factor * 2,
                scale_factor,
                scale_factor * 2,
                self.selected,
                transparency,
            )

    def draw_blocks(self, painter: QPainter, block_length, is_icon):
        for i, image in enumerate(self.blocks):
            x = self.position.x + (i % self.width) if not is_icon else (i % self.width)
            y = self.position.y + (i // self.width) if not is_icon else (i // self.width)

            if is_icon:
                definition = get_enemy_metadata().__root__[self.obj_index]
                x_offset, y_offset = definition.suggested_icon_x_offset, definition.suggested_icon_y_offset
                x -= x_offset
            if not is_icon:
                y_offset = self.height - 1
                y -= y_offset

            block = image.copy()

            mask = block.createMaskFromColor(QColor(*MASK_COLOR).rgb(), Qt.MaskOutColor)
            block.setAlphaChannel(mask)

            # todo better effect
            if self.selected:
                apply_selection_overlay(block, mask)

            if block_length != Block.SIDE_LENGTH:
                block = block.scaled(block_length, block_length)

            painter.drawImage(x * block_length, y * block_length, block)

    def get_status_info(self):
        return [("Name", self.name), ("X", self.position.x), ("Y", self.position.y)]

    def __contains__(self, item):
        x, y = item

        return self.point_in(x, y)

    def point_in(self, x, y):
        return self.rect.contains(x, y)

    def move_by(self, dx, dy):
        self.position = MutablePoint(self.position.x + dx, self.position.y + dy)

    @property
    def position(self) -> PointProtocol:
        return self.enemy.position

    @position.setter
    def position(self, position: PointProtocol):
        self.enemy.position = MutablePoint(max(0, position.x), max(0, position.y))

    @property
    def obj_index(self):
        return self.enemy.type

    @property
    def type(self):
        return self.enemy.type

    def to_bytes(self):
        return bytes(self.enemy)

    def as_image(self) -> QImage:
        definition = get_enemy_metadata().__root__[self.obj_index]
        width, height = definition.suggested_icon_width * 16, definition.suggested_icon_height * 16

        image = QImage(QSize(width, height), QImage.Format_RGBA8888)
        image.fill(QColor(0, 0, 0, 0))

        painter = QPainter(image)

        self.draw(painter, Block.SIDE_LENGTH, True, is_icon=True)

        return image

    def __str__(self):
        return f"{self.name} at {self.position.x}, {self.position.y}"

    def __repr__(self):
        return f"EnemyObject: {self}"
