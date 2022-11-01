from __future__ import annotations

from math import sqrt
from typing import TypeVar

from attr import attrs, evolve
from PySide6.QtCore import QPoint, QPointF, QRect, QSize

from foundry.core.namespace import (
    ConcreteValidator,
    IntegerValidator,
    KeywordValidator,
    NonNegativeIntegerValidator,
    default_validator,
    validate,
)

Vector = TypeVar("Vector", bound="Vector2D")
Point_ = TypeVar("Point_", bound="Point")
Size_ = TypeVar("Size_", bound="Size")
Rect_ = TypeVar("Rect_", bound="Rect")


class Vector2D:
    """
    A vector with two components.
    """

    @property
    def i_component(self) -> int:
        return NotImplemented

    @property
    def j_component(self) -> int:
        return NotImplemented

    @classmethod
    def from_vector(cls: type[Vector], vector: Vector2D) -> Vector:
        return NotImplemented

    @classmethod
    def from_components(cls: type[Vector], i_component: int, j_component: int) -> Vector:
        return NotImplemented

    def __invert__(self: Vector) -> Vector:
        return self.from_components(~self.i_component, ~self.j_component)

    def __neg__(self: Vector) -> Vector:
        return self.from_components(~self.i_component, ~self.j_component)

    def __lshift__(self: Vector, other: int) -> Vector:
        return self.from_components(self.i_component << other, self.j_component << other)

    def __rshift__(self: Vector, other: int) -> Vector:
        return self.from_components(self.i_component >> other, self.j_component >> other)

    def __pow__(self: Vector, other: int) -> Vector:
        return self.from_components(self.i_component**other, self.j_component**other)

    def __add__(self: Vector, other: int | Vector2D) -> Vector:
        if isinstance(other, int):
            return self.from_components(self.i_component + other, self.j_component + other)
        return self.from_components(self.i_component + other.i_component, self.j_component + other.j_component)

    def __sub__(self: Vector, other: int | Vector2D) -> Vector:
        if isinstance(other, int):
            return self.from_components(self.i_component - other, self.j_component - other)
        return self.from_components(self.i_component - other.i_component, self.j_component - other.j_component)

    def __mul__(self: Vector, other: int | Vector2D) -> Vector:
        if isinstance(other, int):
            return self.from_components(self.i_component * other, self.j_component * other)
        return self.from_components(self.i_component * other.i_component, self.j_component * other.j_component)

    def __floordiv__(self: Vector, other: int | Vector2D) -> Vector:
        if isinstance(other, int):
            return self.from_components(self.i_component // other, self.j_component // other)
        return self.from_components(self.i_component // other.i_component, self.j_component // other.j_component)

    def __mod__(self: Vector, other: int | Vector2D) -> Vector:
        if isinstance(other, int):
            return self.from_components(self.i_component % other, self.j_component % other)
        return self.from_components(self.i_component % other.i_component, self.j_component % other.j_component)

    def __and__(self: Vector, other: int | Vector2D) -> Vector:
        if isinstance(other, int):
            return self.from_components(self.i_component & other, self.j_component & other)
        return self.from_components(self.i_component & other.i_component, self.j_component & other.j_component)

    def __or__(self: Vector, other: int | Vector2D) -> Vector:
        if isinstance(other, int):
            return self.from_components(self.i_component | other, self.j_component | other)
        return self.from_components(self.i_component | other.i_component, self.j_component | other.j_component)

    def __xor__(self: Vector, other: int | Vector2D) -> Vector:
        if isinstance(other, int):
            return self.from_components(self.i_component ^ other, self.j_component ^ other)
        return self.from_components(self.i_component ^ other.i_component, self.j_component ^ other.j_component)


@attrs(slots=True, auto_attribs=True, eq=False, frozen=True, hash=True)
@default_validator
class Point(ConcreteValidator, KeywordValidator, Vector2D):
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

    def __eq__(self, other: Point) -> bool:
        return self.x == other.x and self.y == other.y

    def __lt__(self, other: Point) -> bool:
        return self.distance_from_origin < other.distance_from_origin

    def __le__(self, other: Point) -> bool:
        return self.distance_from_origin <= other.distance_from_origin

    def __gt__(self, other: Point) -> bool:
        return self.distance_from_origin > other.distance_from_origin

    def __ge__(self, other: Point) -> bool:
        return self.distance_from_origin >= other.distance_from_origin

    @classmethod
    @validate(x=IntegerValidator, y=IntegerValidator)
    def validate(cls: type[Point_], x: int, y: int) -> Point_:
        return cls(x, y)

    @classmethod
    def from_components(cls: type[Point_], i_component: int, j_component: int) -> Point_:
        """
        Generates a point from the points of a vector.

        Parameters
        ----------
        i_component : int
            The x position of the point.
        j_component : int
            The y position of the point.

        Returns
        -------
        Point_
            The point created from the two components.
        """
        return cls(i_component, j_component)

    @classmethod
    def from_vector(cls: type[Point_], vector: Vector2D) -> Point_:
        """
        Generates a point from a vector.

        Parameters
        ----------
        vector : Vector2D
            The vector with the i and j components representing the x and y positions of the point, respectively.

        Returns
        -------
        Point_
            The point created from the vector.
        """
        return cls(vector.i_component, vector.j_component)

    @classmethod
    def from_qt(cls: type[Point_], point: QPoint | QPointF) -> Point_:
        """
        Generates a point from a QPoint for easy conversion.

        Parameters
        ----------
        point : QPoint | QPointF
            To be converted.

        Returns
        -------
        Point
            Of the QPoint represented inside Python.
        """
        if isinstance(point, QPointF):
            return cls(int(point.x()), int(point.y()))
        return cls(point.x(), point.y())

    @property
    def distance_from_origin(self) -> float:
        """
        The distance this point is from the origin, Point(0, 0).

        Returns
        -------
        float
            The distance from the origin.
        """
        return sqrt(self.x**2 + self.y**2)

    def evolve(self: Point_, *, x: int | None = None, y: int | None = None) -> Point_:
        """
        A convenience method to modify points quicker.

        Parameters
        ----------
        x : int | None, optional
            The x point that can be evolved, by default will not evolve.
        y : int | None, optional
            The y point that can be evolved, by default will not evolve.

        Returns
        -------
        Point_
            The new evolved point.
        """
        return evolve(self, x=self.x if x is None else x, y=self.y if y is None else y)

    def to_qt(self) -> QPoint:
        """
        Converts a point to its PySide equivalent.

        Returns
        -------
        QPoint
            The point in Qt's framework.
        """
        return QPoint(self.x, self.y)


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
@default_validator
class Size(ConcreteValidator, KeywordValidator, Vector2D):
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

    def __lt__(self, other: Size) -> bool:
        return self.width * self.height < other.width * other.height

    def __le__(self, other: Size) -> bool:
        return self.width * self.height <= other.width * other.height

    def __gt__(self, other: Size) -> bool:
        return self.width * self.height > other.width * other.height

    def __ge__(self, other: Size) -> bool:
        return self.width * self.height >= other.width * other.height

    @classmethod
    @validate(width=NonNegativeIntegerValidator, height=NonNegativeIntegerValidator)
    def validate(cls: type[Size_], width: int, height: int) -> Size_:
        return cls(width, height)

    @classmethod
    def from_components(cls: type[Size_], i_component: int, j_component: int) -> Size_:
        """
        Generates a size from the components of a vector.

        Parameters
        ----------
        i_component : int
            The width of the size.
        j_component : int
            The height of the size.

        Returns
        -------
        Size_
            The size created from the two components.
        """
        return cls(i_component, j_component)

    @classmethod
    def from_vector(cls: type[Size_], vector: Vector2D) -> Size_:
        """
        Generates a size from a vector.

        Parameters
        ----------
        vector : Vector2D
            The vector with the i and j components representing the width and height positions of the point,
            respectively.

        Returns
        -------
        Size_
            The size created from the vector.
        """
        return cls(vector.i_component, vector.j_component)

    @classmethod
    def from_qt(cls: type[Size_], size: QSize) -> Size_:
        """
        Generates a size from a QSize for easy conversion.

        Parameters
        ----------
        size : QSize
            To be converted.

        Returns
        -------
        Size_
            Of the QSize represented inside Python.
        """
        return cls(size.width(), size.height())

    def to_qt(self) -> QSize:
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
    def top(self) -> int:
        return max(self.point.y, self.point.y + self.size.height)

    @property
    def bottom(self) -> int:
        return min(self.point.y, self.point.y + self.size.height)

    @property
    def left(self) -> int:
        return min(self.point.x, self.point.x + self.size.width)

    @property
    def right(self) -> int:
        return max(self.point.x, self.point.x + self.size.width)

    @property
    def mid_point(self) -> Point:
        return self.point + (self.size // 2)

    @property
    def upper_left_point(self) -> Point:
        return Point(self.left, self.top)

    @property
    def upper_right_point(self) -> Point:
        return Point(self.right, self.top)

    @property
    def lower_left_point(self) -> Point:
        return Point(self.left, self.bottom)

    @property
    def lower_right_point(self) -> Point:
        return Point(self.right, self.bottom)

    @property
    def vertexes(self) -> list[Point]:
        return [self.upper_left_point, self.upper_right_point, self.lower_left_point, self.lower_right_point]

    @classmethod
    @validate(point=Point, size=Size)
    def validate(cls: type[Rect_], point: Point, size: Size) -> Rect_:
        return cls(point, size)

    @classmethod
    def from_vector(cls, v1: Vector2D, v2: Vector2D):
        return cls(Point.from_vector(v1), Size.from_vector(v2))

    def evolve_top(self, top: int):
        return self.__class__(Point(self.point.x, top), self.size)

    def evolve_bottom(self, bottom: int):
        return self.__class__(self.point, Size(self.size.width, self.point.y - bottom))

    def evolve_left(self, left: int):
        return self.__class__(Point(left, self.point.y), self.size)

    def evolve_right(self, right: int):
        return self.__class__(self.point, Size(self.point.x - right, self.size.height))

    def evolve(
        self, *, top: int | None = None, bottom: int | None = None, left: int | None = None, right: int | None = None
    ):
        rect: Rect = self
        if top is not None:
            rect = rect.evolve_top(top)
        if bottom is not None:
            rect = rect.evolve_bottom(bottom)
        if left is not None:
            rect = rect.evolve_left(left)
        if right is not None:
            rect = rect.evolve_right(right)
        return rect

    def intersects(self, rect: Rect) -> bool:
        return (abs(self.point.x - rect.point.x) * 2 < (self.size.width + rect.size.width)) and (
            abs(self.point.y - rect.point.y) * 2 < (self.size.height + rect.size.height)
        )

    def contains(self, component: Rect | Point) -> bool:
        if isinstance(component, Rect):
            return self.contains(component.upper_left_point) and self.contains(component.lower_right_point)
        return (
            self.point.x <= component.x <= self.point.x + self.size.width
            and self.point.y <= component.y <= self.point.y + self.size.height
        )

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
