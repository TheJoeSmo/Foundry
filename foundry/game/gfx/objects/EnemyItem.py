from PySide6.QtCore import QPointF, QRect, QSize
from PySide6.QtGui import QColor, QImage, QPainter, Qt

from foundry.core.drawable import (
    BLOCK_SIZE,
    MASK_COLOR,
    Sprite,
    apply_selection_overlay,
    sprite_to_image,
)
from foundry.core.geometry import Point, Rect, Size
from foundry.core.graphics_page.GraphicsPage import GraphicsPage
from foundry.core.graphics_set.GraphicsSet import GraphicsSet
from foundry.core.palette import PaletteGroup
from foundry.game.EnemyDefinitions import (
    EnemyDefinition,
    GeneratorType,
    get_enemy_metadata,
)
from foundry.game.gfx.objects.Enemy import Enemy
from foundry.game.gfx.objects.ObjectLike import ObjectLike


class EnemyObject(ObjectLike):
    def __init__(self, data, png_data, palette_group: PaletteGroup):
        super().__init__()
        self.enemy = Enemy.from_bytes(data)

        self.palette_group = palette_group

        self.png_data = png_data

        self.selected = False

        self._render()

    @property
    def definition(self) -> EnemyDefinition:
        return get_enemy_metadata().__root__[self.obj_index]

    @property
    def rect(self) -> Rect:
        bmp_width = (
            self.definition.bmp_width
            if not GeneratorType.SINGLE_SPRITE_OBJECT == self.definition.orientation
            else self.definition.bmp_width // 2
        )
        width = self.definition.rect_width if self.definition.rect_width != 0 else bmp_width
        height = self.definition.rect_height if self.definition.rect_height != 0 else self.definition.bmp_height

        return Rect(
            self.point - Point(self.definition.rect_x_offset, self.definition.rect_y_offset), Size(width, height)
        )

    @property
    def graphics_set(self) -> GraphicsSet:
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
            x = (block_id % 64) * BLOCK_SIZE.width
            y = (block_id // 64) * BLOCK_SIZE.height

            self.blocks.append(self.png_data.copy(QRect(x, y, BLOCK_SIZE.width, BLOCK_SIZE.height)))

    def render(self):
        # nothing to re-render since enemies are just copied over
        pass

    def draw(self, painter: QPainter, block_length, transparency, *, is_icon=False):
        if not GeneratorType.SINGLE_SPRITE_OBJECT == self.definition.orientation:
            self.draw_blocks(painter, block_length, is_icon)
        else:
            self.draw_sprites(painter, block_length // 2, transparency, is_icon)

    def draw_sprites(self, painter: QPainter, scale_factor: int, transparency: bool, is_icon: bool) -> None:
        for i, sprite_info in enumerate(self.sprites):
            if sprite_info.index < 0:
                continue

            x: float = (self.point.x * 2) + (i % self.width) if not is_icon else (i % self.width)
            y: float = self.point.y + (i // self.width) if not is_icon else (i // self.width)
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

            image: QImage = sprite_to_image(
                Sprite(
                    Point(0, 0),
                    sprite_info.index,
                    sprite_info.palette_index,
                    sprite_info.horizontal_mirror,
                    sprite_info.vertical_mirror,
                ),
                self.palette_group,
                self.graphics_set,
                scale_factor // 8,
            )
            if transparency:
                image = image.copy()
                mask: QImage = image.createMaskFromColor(QColor(*MASK_COLOR).rgb(), Qt.MaskMode.MaskOutColor)
                image.setAlphaChannel(mask)

            painter.drawImage(QPointF(x * scale_factor, y * scale_factor * 2), image)

    def draw_blocks(self, painter: QPainter, block_length, is_icon):
        for i, image in enumerate(self.blocks):
            x = self.point.x + (i % self.width) if not is_icon else (i % self.width)
            y = self.point.y + (i // self.width) if not is_icon else (i // self.width)

            if is_icon:
                definition = get_enemy_metadata().__root__[self.obj_index]
                x_offset, y_offset = definition.suggested_icon_x_offset, definition.suggested_icon_y_offset
                x -= x_offset
            if not is_icon:
                y_offset = self.height - 1
                y -= y_offset

            block = image.copy()

            mask = block.createMaskFromColor(QColor(*MASK_COLOR).rgb(), Qt.MaskMode.MaskOutColor)
            block.setAlphaChannel(mask)

            # todo better effect
            if self.selected:
                apply_selection_overlay(block, mask)

            if block_length != BLOCK_SIZE.width:
                block = block.scaled(block_length, block_length)

            painter.drawImage(x * block_length, y * block_length, block)

    def get_status_info(self):
        return [("Name", self.name), ("X", self.point.x), ("Y", self.point.y)]

    def __contains__(self, item: Point) -> bool:
        return self.point_in(item)

    def point_in(self, point: Point) -> bool:
        return point in self.rect

    def move_by(self, point: Point) -> None:
        self.point = self.point + point

    @property
    def point(self) -> Point:
        return self.enemy.point

    @point.setter
    def point(self, point: Point):
        self.enemy.point = Point(max(0, point.x), max(0, point.y))

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

        image = QImage(QSize(width, height), QImage.Format.Format_RGBA8888)
        image.fill(QColor(0, 0, 0, 0))

        painter = QPainter(image)

        self.draw(painter, BLOCK_SIZE.width, True, is_icon=True)

        return image

    def __str__(self):
        return f"{self.name} at {self.point}"

    def __repr__(self):
        return f"EnemyObject: {self}"
