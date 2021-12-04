from PySide6.QtCore import QRect
from PySide6.QtGui import QImage

from foundry import data_dir
from foundry.game.gfx.drawable.Block import Block
from foundry.game.gfx.objects.EnemyItem import EnemyObject
from foundry.game.gfx.Palette import PALETTE_GROUPS_PER_OBJECT_SET, load_palette_group


class EnemyItemFactory:
    object_set: int
    graphic_set: int

    definitions: list = []

    def __init__(self, object_set: int, palette_index: int):
        png = QImage(str(data_dir.joinpath("gfx.png")))

        png.convertTo(QImage.Format_RGB888)

        rows_per_object_set = 256 // 64

        y_offset = 12 * rows_per_object_set * Block.HEIGHT

        self.png_data = png.copy(QRect(0, y_offset, png.width(), png.height() - y_offset))

        self.palette_group = load_palette_group(object_set, PALETTE_GROUPS_PER_OBJECT_SET + palette_index)

    def from_data(self, data, _):
        return EnemyObject(data, self.png_data, self.palette_group)

    def from_properties(self, enemy_item_id: int, x: int, y: int):
        data = bytearray(3)

        data[0] = enemy_item_id
        data[1] = x
        data[2] = y

        obj = self.from_data(data, 0)

        return obj
