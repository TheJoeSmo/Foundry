from __future__ import annotations

from math import sqrt
from typing import Any, ClassVar, Type, TypeVar

from attr import attrs
from PySide6.QtCore import QPoint, QRect

from foundry.core.namespace import (
    ConcreteValidator,
    IntegerValidator,
    MetaValidator,
    NonNegativeIntegerValidator,
    TypeHandler,
)

_P = TypeVar("_P", bound="Point")
_S = TypeVar("_S", bound="Size")
_R = TypeVar("_R", bound="Rect")


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class Point(ConcreteValidator):
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
    __type_default__: ClassVar[str] = "DEFAULT"
    __names__: ClassVar[tuple[str, ...]] = ("__POINT_VALIDATOR__", "point", "Point", "POINT")

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
    def validate(cls: Type[_P], values: Any) -> _P:
        kwargs = cls.check_for_kwargs_only(values, "x", "y")
        x: int = cls.validate_other_type(IntegerValidator, kwargs.get("parent", None), kwargs["x"])
        y: int = cls.validate_other_type(IntegerValidator, kwargs.get("parent", None), kwargs["y"])
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


def _validate_point(class_: Type[_P], v) -> _P:
    return class_.validate(v)


Point.__validator_handler__ = TypeHandler({"DEFAULT": MetaValidator(_validate_point)})


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class Size(ConcreteValidator):
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

    __type_default__: ClassVar[str] = "DEFAULT"
    __names__: ClassVar[tuple[str, ...]] = ("__SIZE_VALIDATOR__", "size", "Size", "SIZE")

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
    def validate(cls: Type[_S], values) -> _S:
        kwargs = cls.check_for_kwargs_only(values, "width", "height")
        width: int = cls.validate_other_type(NonNegativeIntegerValidator, kwargs.get("parent", None), kwargs["width"])
        height: int = cls.validate_other_type(NonNegativeIntegerValidator, kwargs.get("parent", None), kwargs["height"])
        return cls(width, height)


def _validate_size(class_: Type[_S], v) -> _S:
    return class_.validate(v)


Size.__validator_handler__ = TypeHandler({"DEFAULT": MetaValidator(_validate_size)})


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class Rect(ConcreteValidator):
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

    __type_default__: ClassVar[str] = "DEFAULT"
    __names__: ClassVar[tuple[str, ...]] = ("__RECT_VALIDATOR__", "rect", "Rect", "Rect")

    @classmethod
    def validate(cls: Type[_R], values) -> _R:
        kwargs = cls.check_for_kwargs_only(values, "point", "size")
        point: Point = cls.validate_other_type(Point, kwargs.get("parent", None), kwargs["point"])
        size: Size = cls.validate_other_type(Size, kwargs.get("parent", None), kwargs["size"])
        return cls(point, size)


def _validate_rect(class_: Type[_R], v) -> _R:
    return class_.validate(v)


Rect.__validator_handler__ = TypeHandler({"DEFAULT": MetaValidator(_validate_rect)})


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
