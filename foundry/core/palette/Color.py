from attr import attrs, field, validators
from PySide6.QtGui import QColor

from foundry.core.namespace import (
    ConcreteValidator,
    IntegerValidator,
    KeywordValidator,
    default_validator,
    validate,
)


def _check_in_color_range(inst, attr, value):
    if not 0 <= value <= 0xFF:
        raise ValueError(f"{value} is not inside the range 0-255")
    return value


@attrs(slots=True, frozen=True, eq=True, hash=True)
@default_validator
class Color(ConcreteValidator, KeywordValidator):
    __names__ = ("__COLOR_VALIDATOR__", "color", "Color", "COLOR")
    __required_validators__ = (IntegerValidator,)

    red: int = field(validator=[validators.instance_of(int), _check_in_color_range])
    green: int = field(validator=[validators.instance_of(int), _check_in_color_range])
    blue: int = field(validator=[validators.instance_of(int), _check_in_color_range])
    alpha: int = field(default=255, validator=[validators.instance_of(int), _check_in_color_range])

    @classmethod
    @validate(red=IntegerValidator, green=IntegerValidator, blue=IntegerValidator, alpha=IntegerValidator)
    def validate(cls, red: int, green: int, blue: int, alpha: int):
        return cls(red, green, blue, alpha)

    @property
    def qcolor(self) -> QColor:
        return QColor(self.red, self.green, self.blue, self.alpha)
