from __future__ import annotations

from math import sqrt

from attr import attrs
from pydantic.errors import MissingError
from pydantic.validators import int_validator
from PySide6.QtCore import QPoint


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
