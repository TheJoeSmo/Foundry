from PySide6.QtCore import QRect
from PySide6.QtGui import QImage

from foundry import data_dir
from foundry.core.drawable import BLOCK_SIZE
from foundry.core.geometry import Point
from foundry.core.palette import PALETTE_GROUPS_PER_OBJECT_SET, PaletteGroup
from foundry.game.gfx.objects.EnemyItem import EnemyObject


class EnemyItemFactory:
    object_set: int
    graphic_set: int

    definitions: list = []

    def __init__(self, object_set: int, palette_index: int):
        png = QImage(str(data_dir.joinpath("gfx.png")))

        png.convertTo(QImage.Format.Format_RGB888)

        rows_per_object_set = 256 // 64

        y_offset = 12 * rows_per_object_set * BLOCK_SIZE.height

        self.png_data = png.copy(QRect(0, y_offset, png.width(), png.height() - y_offset))

        self.palette_group = PaletteGroup.from_tileset(object_set, PALETTE_GROUPS_PER_OBJECT_SET + palette_index)

    def from_data(self, data, _):
        return EnemyObject(data, self.png_data, self.palette_group)

    def from_properties(self, enemy_item_id: int, point: Point):
        data = bytearray(3)

        data[0] = enemy_item_id
        data[1] = point.x
        data[2] = point.y

        obj = self.from_data(data, 0)

        return obj
