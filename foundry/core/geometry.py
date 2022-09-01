from __future__ import annotations

from math import sqrt
from typing import TypeVar

from attr import attrs
from PySide6.QtCore import QPoint, QRect, QSize

from foundry.core.namespace import (
    ConcreteValidator,
    IntegerValidator,
    KeywordValidator,
    NonNegativeIntegerValidator,
    default_validator,
    validate,
)

_P = TypeVar("_P", bound="Point")
_S = TypeVar("_S", bound="Size")
_R = TypeVar("_R", bound="Rect")


@attrs(slots=True, auto_attribs=True, eq=False, frozen=True, hash=True)
@default_validator
class Point(ConcreteValidator, KeywordValidator):
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
    __names__ = ("__POINT_VALIDATOR__", "point", "Point", "POINT")
    __required_validators__ = (IntegerValidator,)

    def __eq__(self, other: Point):
        return self.x == other.x and self.y == other.y

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
    @validate(x=IntegerValidator, y=IntegerValidator)
    def validate(cls: type[_P], x: int, y: int) -> _P:
        return cls(x, y)

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
@default_validator
class Size(ConcreteValidator, KeywordValidator):
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
    __names__ = ("__SIZE_VALIDATOR__", "size", "Size", "SIZE")
    __required_validators__ = (NonNegativeIntegerValidator,)

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

    def __add__(self, other: Size | int) -> Size:
        if isinstance(other, Size):
            return self.__class__(self.width + other.width, self.height + other.height)
        elif isinstance(other, int):
            return self.__class__(self.width + other, self.height + other)
        return NotImplemented

    def __sub__(self, other: Size | int) -> Size:
        if isinstance(other, Size):
            return self.__class__(self.width - other.width, self.height - other.height)
        elif isinstance(other, int):
            return self.__class__(self.width - other, self.height - other)
        return NotImplemented

    def __mul__(self, other: Size | int) -> Size:
        if isinstance(other, Size):
            return self.__class__(self.width * other.width, self.height * other.height)
        elif isinstance(other, int):
            return self.__class__(self.width * other, self.height * other)
        return NotImplemented

    def __floordiv__(self, other: Size) -> Size:
        if isinstance(other, Size):
            return self.__class__(self.width // other.width, self.height // other.height)
        elif isinstance(other, int):
            return self.__class__(self.width // other, self.height // other)
        return NotImplemented

    def __mod__(self, other: Size) -> Size:
        if isinstance(other, Size):
            return self.__class__(self.width % other.width, self.height % other.height)
        elif isinstance(other, int):
            return self.__class__(self.width % other, self.height % other)
        return NotImplemented

    def __and__(self, other: Size) -> Size:
        if isinstance(other, Size):
            return self.__class__(self.width & other.width, self.height & other.height)
        elif isinstance(other, int):
            return self.__class__(self.width & other, self.height & other)
        return NotImplemented

    def __or__(self, other: Size) -> Size:
        if isinstance(other, Size):
            return self.__class__(self.width | other.width, self.height | other.height)
        elif isinstance(other, int):
            return self.__class__(self.width | other, self.height | other)
        return NotImplemented

    def __xor__(self, other: Size) -> Size:
        if isinstance(other, Size):
            return self.__class__(self.width ^ other.width, self.height ^ other.height)
        elif isinstance(other, int):
            return self.__class__(self.width ^ other, self.height ^ other)
        return NotImplemented

    @classmethod
    @validate(width=NonNegativeIntegerValidator, height=NonNegativeIntegerValidator)
    def validate(cls: type[_S], width: int, height: int) -> _S:
        return cls(width, height)

    @classmethod
    def from_qsize(cls, size: QSize):
        """
        Generates a size from a QSize for easy conversion.

        Parameters
        ----------
        size : QSize
            To be converted.

        Returns
        -------
        Size
            Of the QSize represented inside Python.
        """
        return cls(size.width(), size.height())

    @property
    def qsize(self) -> QSize:
        """
        Generates a QSize from a Size.

        Parameters
        ----------
        rect : Size
            The rect to be converted to a Size.

        Returns
        -------
        QSize
            The QSize derived from the Size.
        """
        return QSize(self.width, self.height)


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
@default_validator
class Rect(ConcreteValidator, KeywordValidator):
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
    __names__ = ("__RECT_VALIDATOR__", "rect", "Rect", "Rect")
    __required_validators__ = (Point, Size)

    @property
    def qrect(self) -> QRect:
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
        return QRect(self.point.x, self.point.y, self.size.width, self.size.height)

    @classmethod
    @validate(point=Point, size=Size)
    def validate(cls: type[_R], point: Point, size: Size) -> _R:
        return cls(point, size)
