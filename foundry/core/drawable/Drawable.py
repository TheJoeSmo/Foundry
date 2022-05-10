from typing import Protocol

from pydantic import BaseModel
from PySide6.QtGui import QImage

from foundry.core.drawable import DrawableType
from foundry.core.geometry import Point, Size


class DrawableProtocol(Protocol):
    """
    An element that can be drawn to the screen.
    """

    point_offset: Point

    @property
    def size(self) -> Size:
        ...

    def image(self, scale_factor: int = 1) -> QImage:
        ...


class Drawable(BaseModel):
    type: DrawableType
    point_offset: Point = Point(x=0, y=0)

    class Config:
        use_enum_values = True
