from functools import cached_property
from typing import Protocol

from attr import attrs, field
from pydantic import BaseModel, validator
from PySide6.QtGui import QColor


class ColorProtocol(Protocol):
    red: int
    blue: int
    green: int
    alpha: int


@attrs(slots=True, frozen=True, eq=True, hash=True)
class Color:
    red: int = field(validator=[attrs.validators.instance_of(int), attrs.validators.le(0x100), attrs.validators.ge(0)])
    blue: int = field(validator=[attrs.validators.instance_of(int), attrs.validators.le(0x100), attrs.validators.ge(0)])
    green: int = field(
        validator=[attrs.validators.instance_of(int), attrs.validators.le(0x100), attrs.validators.ge(0)]
    )
    alpha: int = field(
        default=255, validator=[attrs.validators.instance_of(int), attrs.validators.le(0x100), attrs.validators.ge(0)]
    )

    @cached_property
    def qcolor(self) -> QColor:
        return QColor(self.red, self.green, self.blue, self.alpha)


class PydanticColor(BaseModel):
    red: int
    blue: int
    green: int
    alpha: int

    @validator("red", "blue", "green", "alpha")
    def check_color_range(cls, v):
        if not 0 <= v <= 0xFF:
            raise ValueError(f"{v} is not inside the range 0-255")
        return v
