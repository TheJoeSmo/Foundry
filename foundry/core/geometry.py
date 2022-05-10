from __future__ import annotations

from math import sqrt

from attr import attrs
from pydantic.errors import MissingError, NumberNotGeError
from pydantic.validators import int_validator
from PySide6.QtCore import QPoint, QRect


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class Point:
    """
    A two dimensional representation of a point on a plain.

    Attributes
    ----------
    x: int
        The horizontal location of the point.
    y: int
        The vertical location of the point.
    """

    x: int
    y: int

    def __lt__(self, other: Point):
        return self.distance_from_origin < other.distance_from_origin

    def __le__(self, other: Point):
        return self.distance_from_origin <= other.distance_from_origin

    def __gt__(self, other: Point):
        return self.distance_from_origin > other.distance_from_origin

    def __ge__(self, other: Point):
        return self.distance_from_origin >= other.distance_from_origin

    def __invert__(self) -> Point:
        return self.__class__(~self.x, ~self.y)

    def __neg__(self) -> Point:
        return self.__class__(~self.x, ~self.y)

    def __lshift__(self, other: int) -> Point:
        return self.__class__(self.x << other, self.y << other)

    def __rshift__(self, other: int) -> Point:
        return self.__class__(self.x >> other, self.y >> other)

    def __pow__(self, other: int) -> Point:
        return self.__class__(self.x**other, self.y**other)

    def __add__(self, other: Point) -> Point:
        return self.__class__(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Point) -> Point:
        return self.__class__(self.x - other.x, self.y - other.y)

    def __mul__(self, other: Point) -> Point:
        return self.__class__(self.x * other.x, self.y * other.y)

    def __floordiv__(self, other: Point) -> Point:
        return self.__class__(self.x // other.x, self.y // other.y)

    def __mod__(self, other: Point) -> Point:
        return self.__class__(self.x % other.x, self.y % other.y)

    def __and__(self, other: Point) -> Point:
        return self.__class__(self.x & other.x, self.y & other.y)

    def __or__(self, other: Point) -> Point:
        return self.__class__(self.x | other.x, self.y | other.y)

    def __xor__(self, other: Point) -> Point:
        return self.__class__(self.x ^ other.x, self.y ^ other.y)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, values) -> Point:
        if "x" not in values:
            MissingError()
        if "y" not in values:
            MissingError()
        x: int = int_validator(values["x"])
        y: int = int_validator(values["y"])
        return Point(x, y)

    @classmethod
    def from_qpoint(cls, point: QPoint) -> Point:
        """
        Generates a point from a QPoint for easy conversion.

        Parameters
        ----------
        point : QPoint
            To be converted.

        Returns
        -------
        AbstractPoint
            Of the QPoint represented inside Python.
        """
        return cls(point.x(), point.y())

    @property
    def distance_from_origin(self) -> float:
        return sqrt(self.x**2 + self.y**2)


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


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class Rect:
    """
    A two dimensional representation of a box, that uses ``attrs`` to create a basic
    implementation.

    Attributes
    ----------
    point: Point
        The upper left corner of the rect.
    size: Size
        The size of the box.
    """

    point: Point
    size: Size

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, values) -> Rect:
        if "point" not in values:
            MissingError()
        if "size" not in values:
            MissingError()
        return Rect(Point.validate(values["point"]), Size.validate(values["size"]))


def to_qrect(rect: Rect) -> QRect:
    """
    Generates a QRect from a Rect.

    Parameters
    ----------
    rect : Rect
        The rect to be converted to a Rect.

    Returns
    -------
    QRect
        The QRect derived from the Rect.
    """
    return QRect(rect.point.x, rect.point.y, rect.size.width, rect.size.height)
