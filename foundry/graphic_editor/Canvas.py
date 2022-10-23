from __future__ import annotations

from attr import Factory, attrs
from numpy import int16, zeros
from numpy.typing import NDArray
from PySide6.QtGui import QPaintEvent

from foundry.core.geometry import Point, Size
from foundry.core.gui import BaseModel
from foundry.core.painter.Painter import Painter
from foundry.core.palette import Color, Palette
from foundry.gui.core import GridMouseHandler, Widget


class Canvas(GridMouseHandler, Widget):
    model: Model
    bitmap: NDArray
    bitmap_palette: Palette
    zoom: int

    @attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
    class Model(BaseModel):
        bitmap: NDArray = Factory(lambda: zeros((256, 256), dtype=int16))
        bitmap_palette: Palette = Factory(Palette.as_empty)
        zoom: int = 16

    @property
    def grid_size(self) -> Size:
        return Size(self.bitmap.shape[1], self.bitmap.shape[0])

    @property
    def grid_scale(self) -> Size:
        return Size(self.zoom, self.zoom)

    def paintEvent(self, event: QPaintEvent):
        pixel_size: Size = self.grid_scale
        with Painter(self) as painter:
            for x in range(self.grid_size.width):
                for y in range(self.grid_size.height):
                    painter.setBrush(self.bitmap_palette.colors[self.bitmap[x, y]])
                    painter.drawRect(pixel_size.width * x, pixel_size.height * y, pixel_size.width, pixel_size.height)

    def draw_point(self, point: Point, color: int | Color):
        if isinstance(color, Color):
            color = self.bitmap_palette.color_palette.colors.index(color)
        self.bitmap[point.y, point.x] = color
