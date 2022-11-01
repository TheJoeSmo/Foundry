from __future__ import annotations

from math import sqrt
from typing import Protocol, TypeVar

from attr import attrs
from PySide6.QtCore import QPoint, QPointF, QRect, QSize

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


class Vector2D(Protocol):
    @property
    def i_component(self) -> int:
        ...

    @property
    def j_component(self) -> int:
        ...


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

    @property
    def i_component(self) -> int:
        return self.x

    @property
    def j_component(self) -> int:
        return self.y

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

    def __add__(self, other: Vector2D) -> Point:
        return self.__class__(self.x + other.i_component, self.y + other.j_component)

    def __sub__(self, other: Vector2D) -> Point:
        return self.__class__(self.x - other.i_component, self.y - other.j_component)

    def __mul__(self, other: Vector2D) -> Point:
        return self.__class__(self.x * other.i_component, self.y * other.j_component)

    def __floordiv__(self, other: Vector2D) -> Point:
        return self.__class__(self.x // other.i_component, self.y // other.j_component)

    def __mod__(self, other: Vector2D) -> Point:
        return self.__class__(self.x % other.i_component, self.y % other.j_component)

    def __and__(self, other: Vector2D) -> Point:
        return self.__class__(self.x & other.i_component, self.y & other.j_component)

    def __or__(self, other: Vector2D) -> Point:
        return self.__class__(self.x | other.i_component, self.y | other.j_component)

    def __xor__(self, other: Vector2D) -> Point:
        return self.__class__(self.x ^ other.i_component, self.y ^ other.j_component)

    @classmethod
    @validate(x=IntegerValidator, y=IntegerValidator)
    def validate(cls: type[_P], x: int, y: int) -> _P:
        return cls(x, y)

    @classmethod
    def from_vector(cls, vector: Vector2D):
        return cls(vector.i_component, vector.j_component)

    @classmethod
    def from_qt(cls, point: QPoint | QPointF) -> Point:
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
        if isinstance(point, QPointF):
            return cls(int(point.x()), int(point.y()))
        return cls(point.x(), point.y())

    @property
    def distance_from_origin(self) -> float:
        return sqrt(self.x**2 + self.y**2)

    def to_qt(self) -> QPoint:
        return QPoint(self.x, self.y)


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

    @property
    def i_component(self) -> int:
        return self.width

    @property
    def j_component(self) -> int:
        return self.height

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

    def __add__(self, other: Vector2D | int) -> Size:
        if isinstance(other, int):
            return self.__class__(self.width + other, self.height + other)
        return self.__class__(self.width + other.i_component, self.height + other.j_component)

    def __sub__(self, other: Vector2D | int) -> Size:
        if isinstance(other, int):
            return self.__class__(self.width - other, self.height - other)
        return self.__class__(self.width - other.i_component, self.height - other.j_component)

    def __mul__(self, other: Vector2D | int) -> Size:
        if isinstance(other, int):
            return self.__class__(self.width * other, self.height * other)
        return self.__class__(self.width * other.i_component, self.height * other.j_component)

    def __floordiv__(self, other: Vector2D | int) -> Size:
        if isinstance(other, int):
            return self.__class__(self.width // other, self.height // other)
        return self.__class__(self.width // other.i_component, self.height // other.j_component)

    def __mod__(self, other: Vector2D) -> Size:
        if isinstance(other, int):
            return self.__class__(self.width % other, self.height % other)
        return self.__class__(self.width % other.i_component, self.height % other.j_component)

    def __and__(self, other: Vector2D) -> Size:
        if isinstance(other, int):
            return self.__class__(self.width & other, self.height & other)
        return self.__class__(self.width & other.i_component, self.height & other.j_component)

    def __or__(self, other: Vector2D) -> Size:
        if isinstance(other, int):
            return self.__class__(self.width | other, self.height | other)
        return self.__class__(self.width | other.i_component, self.height | other.j_component)

    def __xor__(self, other: Vector2D) -> Size:
        if isinstance(other, int):
            return self.__class__(self.width ^ other, self.height ^ other)
        return self.__class__(self.width ^ other.i_component, self.height ^ other.j_component)

    @classmethod
    @validate(width=NonNegativeIntegerValidator, height=NonNegativeIntegerValidator)
    def validate(cls: type[_S], width: int, height: int) -> _S:
        return cls(width, height)

    @classmethod
    def from_vector(cls, vector: Vector2D):
        return cls(vector.i_component, vector.j_component)

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

    def __add__(self, other: Rect | Vector2D):
        if isinstance(other, Rect):
            return self.__class__(self.point + other.point, self.size + other.size)
        return self.__class__(self.point + other, self.size + other)

    def __sub__(self, other: Rect | Vector2D):
        if isinstance(other, Rect):
            return self.__class__(self.point - other.point, self.size - other.size)
        return self.__class__(self.point - other, self.size - other)

    def __mul__(self, other: Rect | Vector2D):
        if isinstance(other, Rect):
            return self.__class__(self.point * other.point, self.size * other.size)
        return self.__class__(self.point * other, self.size * other)

    def __floordiv__(self, other: Rect | Vector2D):
        if isinstance(other, Rect):
            return self.__class__(self.point // other.point, self.size // other.size)
        return self.__class__(self.point // other, self.size // other)

    def __mod__(self, other: Vector2D):
        if isinstance(other, Rect):
            return self.__class__(self.point % other.point, self.size % other.size)
        return self.__class__(self.point % other, self.size % other)

    @property
    def upper_left_point(self) -> Point:
        return self.point

    @property
    def upper_right_point(self) -> Point:
        return Point(self.point.x + self.size.width, self.point.y)

    @property
    def lower_left_point(self) -> Point:
        return Point(self.point.x, self.point.y + self.size.height)

    @property
    def lower_right_point(self) -> Point:
        return self.point + self.size

    @classmethod
    @validate(point=Point, size=Size)
    def validate(cls: type[_R], point: Point, size: Size) -> _R:
        return cls(point, size)

    @classmethod
    def from_vector(cls, v1: Vector2D, v2: Vector2D):
        return cls(Point.from_vector(v1), Size.from_vector(v2))

    def to_qt(self) -> QRect:
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
