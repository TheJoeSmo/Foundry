from functools import cached_property
from typing import Protocol

from attr import attrs, field, validators
from pydantic import BaseModel, validator
from PySide6.QtGui import QColor


class ColorProtocol(Protocol):
    red: int
    green: int
    blue: int
    alpha: int

    @property
    def qcolor(self) -> QColor:
        return QColor(self.red, self.green, self.blue, self.alpha)


def _check_in_color_range(inst, attr, value):
    if not 0 <= value <= 0xFF:
        raise ValueError(f"{value} is not inside the range 0-255")
    return value


@attrs(slots=True, frozen=True, eq=True, hash=True)
class Color:
    red: int = field(validator=[validators.instance_of(int), _check_in_color_range])
    green: int = field(validator=[validators.instance_of(int), _check_in_color_range])
    blue: int = field(validator=[validators.instance_of(int), _check_in_color_range])
    alpha: int = field(default=255, validator=[validators.instance_of(int), _check_in_color_range])

    @property
    def qcolor(self) -> QColor:
        return QColor(self.red, self.green, self.blue, self.alpha)


class PydanticColor(BaseModel):
    red: int
    green: int
    blue: int
    alpha: int = 255

    # Enable cached property to be ignored by Pydantic
    class Config:
        arbitrary_types_allowed = True
        keep_untouched = (cached_property,)

    @validator("red", "blue", "green", "alpha", allow_reuse=True)
    def check_color_range(cls, v):
        if not 0 <= v <= 0xFF:
            raise ValueError(f"{v} is not inside the range 0-255")
        return v

    @cached_property
    def color(self) -> ColorProtocol:
        return Color(self.red, self.green, self.blue, self.alpha)
