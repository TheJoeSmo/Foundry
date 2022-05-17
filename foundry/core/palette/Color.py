from __future__ import annotations

from attr import attrs, field, validators
from pydantic.errors import MissingError, NumberNotGeError, NumberNotLeError
from pydantic.validators import int_validator
from PySide6.QtGui import QColor


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

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, values) -> Color:
        if "red" not in values:
            MissingError()
        if "green" not in values:
            MissingError()
        if "blue" not in values:
            MissingError()
        red: int = int_validator(values["red"])
        green: int = int_validator(values["green"])
        blue: int = int_validator(values["blue"])
        alpha: int = int_validator(values["alpha"]) if "alpha" in values else 255
        if any(color < 0 for color in [red, green, blue, alpha]):
            raise NumberNotGeError(limit_value=0)
        if any(color > 255 for color in [red, green, blue, alpha]):
            raise NumberNotLeError(limit_value=255)
        return Color(red, green, blue, alpha)
