from __future__ import annotations

from attr import attrs
from pydantic.errors import MissingError, NumberNotGeError
from pydantic.validators import int_validator


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class Size:
    """
    A two dimensional representation of a size.

    Attributes
    ----------
    width: int
        The width of the object being represented.
    height: int
        The height of the object being represented.
    """

    width: int
    height: int

    def __lt__(self, other: Size):
        return self.width * self.height < other.width * other.height

    def __le__(self, other: Size):
        return self.width * self.height <= other.width * other.height

    def __gt__(self, other: Size):
        return self.width * self.height > other.width * other.height

    def __ge__(self, other: Size):
        return self.width * self.height >= other.width * other.height

    def __invert__(self) -> Size:
        return self.__class__(~self.width, ~self.height)

    def __neg__(self) -> Size:
        return self.__class__(~self.width, ~self.height)

    def __lshift__(self, other: int) -> Size:
        return self.__class__(self.width << other, self.height << other)

    def __rshift__(self, other: int) -> Size:
        return self.__class__(self.width >> other, self.height >> other)

    def __pow__(self, other: int) -> Size:
        return self.__class__(self.width**other, self.height**other)

    def __add__(self, other: Size) -> Size:
        return self.__class__(self.width + other.width, self.height + other.height)

    def __sub__(self, other: Size) -> Size:
        return self.__class__(self.width - other.width, self.height - other.height)

    def __mul__(self, other: Size) -> Size:
        return self.__class__(self.width * other.width, self.height * other.height)

    def __floordiv__(self, other: Size) -> Size:
        return self.__class__(self.width // other.width, self.height // other.height)

    def __mod__(self, other: Size) -> Size:
        return self.__class__(self.width % other.width, self.height % other.height)

    def __and__(self, other: Size) -> Size:
        return self.__class__(self.width & other.width, self.height & other.height)

    def __or__(self, other: Size) -> Size:
        return self.__class__(self.width | other.width, self.height | other.height)

    def __xor__(self, other: Size) -> Size:
        return self.__class__(self.width ^ other.width, self.height ^ other.height)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, values) -> Size:
        if "width" not in values:
            MissingError()
        if "height" not in values:
            MissingError()
        width: int = int_validator(values["width"])
        height: int = int_validator(values["height"])
        if width < 0:
            raise NumberNotGeError(limit_value=0)
        if height < 0:
            raise NumberNotGeError(limit_value=0)
        return Size(width, height)
