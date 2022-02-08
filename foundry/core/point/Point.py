from abc import ABC, abstractmethod
from math import sqrt
from typing import Protocol, Type, TypeVar

from attr import attrs
from pydantic import BaseModel
from PySide6.QtCore import QPoint


class PointProtocol(Protocol):
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

    @property
    def distance_from_origin(self) -> float:
        ...


class HashablePointProtocol(PointProtocol, Protocol):
    def __hash__(self) -> int:
        ...


_T = TypeVar("_T", bound="AbstractPoint")


class AbstractPoint(ABC):
    x: int
    y: int

    @classmethod
    @abstractmethod
    def from_values(cls: Type[_T], x: int, y: int) -> _T:
        """
        A generalized way to create itself from an x and y.

        Returns
        -------
        AbstractPoint
            The created point from the x and y.
        """
        ...

    @classmethod
    def from_point(cls: Type[_T], point: PointProtocol) -> _T:
        """
        Generates a point from a point protocol.

        Parameters
        ----------
        point : PointProtocol
            The point protocol to be converted to this type.

        Returns
        -------
        AbstractPoint
            Of the same point protocol mapped to this type.
        """
        return cls.from_values(point.x, point.y)

    @classmethod
    def from_qpoint(cls: Type[_T], point: QPoint) -> _T:
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
        return cls.from_values(point.x(), point.y())

    @property
    def distance_from_origin(self) -> float:
        return sqrt(self.x ** 2 + self.y ** 2)

    def __lt__(self, other: PointProtocol):
        return self.distance_from_origin < other.distance_from_origin

    def __le__(self, other: PointProtocol):
        return self.distance_from_origin <= other.distance_from_origin

    def __gt__(self, other: PointProtocol):
        return self.distance_from_origin > other.distance_from_origin

    def __ge__(self, other: PointProtocol):
        return self.distance_from_origin >= other.distance_from_origin

    def __invert__(self: _T) -> _T:
        return self.from_values(~self.x, ~self.y)

    def __neg__(self: _T) -> _T:
        return self.from_values(~self.x, ~self.y)

    def __lshift__(self: _T, other: int) -> _T:
        return self.from_values(self.x << other, self.y << other)

    def __rshift__(self: _T, other: int) -> _T:
        return self.from_values(self.x >> other, self.y >> other)

    def __pow__(self: _T, other: int) -> _T:
        return self.from_values(self.x ** other, self.y ** other)

    def __add__(self: _T, other: PointProtocol) -> _T:
        return self.from_values(self.x + other.x, self.y + other.y)

    def __sub__(self: _T, other: PointProtocol) -> _T:
        return self.from_values(self.x - other.x, self.y - other.y)

    def __mul__(self: _T, other: PointProtocol) -> _T:
        return self.from_values(self.x * other.x, self.y * other.y)

    def __floordiv__(self: _T, other: PointProtocol) -> _T:
        return self.from_values(self.x // other.x, self.y // other.y)

    def __mod__(self: _T, other: PointProtocol) -> _T:
        return self.from_values(self.x % other.x, self.y % other.y)

    def __and__(self: _T, other: PointProtocol) -> _T:
        return self.from_values(self.x & other.x, self.y & other.y)

    def __or__(self: _T, other: PointProtocol) -> _T:
        return self.from_values(self.x | other.x, self.y | other.y)

    def __xor__(self: _T, other: PointProtocol) -> _T:
        return self.from_values(self.x ^ other.x, self.y ^ other.y)


_MT = TypeVar("_MT", bound="MutablePoint")


@attrs(slots=True, auto_attribs=True, eq=True)
class MutablePoint(AbstractPoint):
    """
    A two dimensional representation of a point on a plain, that uses ``attrs`` to create a basic
    implementation.

    Attributes
    ----------
    x: int
        The horizontal location of the point.
    y: int
        The vertical location of the point.
    """

    x: int
    y: int

    @classmethod
    def from_values(cls: Type[_MT], x: int, y: int) -> _MT:
        return cls(x, y)


_IT = TypeVar("_IT", bound="Point")


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class Point(AbstractPoint):
    """
    A two dimensional representation of a point on a plain, that uses ``attrs`` to create a basic
    implementation.

    Attributes
    ----------
    x: int
        The horizontal location of the point.
    y: int
        The vertical location of the point.
    """

    x: int
    y: int

    @classmethod
    def from_values(cls: Type[_IT], x: int, y: int) -> _IT:
        return cls(x, y)


class PydanticPoint(BaseModel):
    x: int
    y: int

    @property
    def point(self) -> PointProtocol:
        return Point(self.x, self.y)
