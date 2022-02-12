from typing import Protocol

from pydantic import BaseModel
from PySide6.QtGui import QImage

from foundry.core.drawable import DrawableType
from foundry.core.point.Point import PointProtocol, PydanticPoint
from foundry.core.size.Size import SizeProtocol


class DrawableProtocol(Protocol):
    """
    An element that can be drawn to the screen.
    """

    point_offset: PointProtocol

    @property
    def size(self) -> SizeProtocol:
        ...

    def image(self, scale_factor: int = 1) -> QImage:
        ...


class Drawable(BaseModel):
    type: DrawableType
    point_offset: PydanticPoint = PydanticPoint(x=0, y=0)

    @property
    def drawable(self) -> DrawableProtocol:
        raise NotImplementedError

    class Config:
        use_enum_values = True
