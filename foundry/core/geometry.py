from __future__ import annotations

from collections.abc import Sequence
from math import sqrt
from typing import Self

from attr import attrs, evolve, field
from attr.validators import ge
from PySide6.QtCore import QPoint, QPointF, QRect, QSize

from foundry.core.namespace import (
    ConcreteValidator,
    IntegerValidator,
    KeywordValidator,
    NonNegativeIntegerValidator,
    default_validator,
    validate,
)


@attrs(slots=True, auto_attribs=True, eq=False, frozen=True, hash=False)
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
    def from_vector(cls, vector: Vector2D) -> Self:
        return NotImplemented

    @classmethod
    def from_components(cls, i_component: int, j_component: int) -> Self:
        return NotImplemented

    def __invert__(self) -> Self:
        return self.from_components(~self.i_component, ~self.j_component)

    def __neg__(self) -> Self:
        return self.from_components(~self.i_component, ~self.j_component)

    def __lshift__(self, other: int) -> Self:
        return self.from_components(self.i_component << other, self.j_component << other)

    def __rshift__(self, other: int) -> Self:
        return self.from_components(self.i_component >> other, self.j_component >> other)

    def __pow__(self, other: int) -> Self:
        return self.from_components(self.i_component**other, self.j_component**other)

    def __add__(self, other: int | Vector2D) -> Self:
        if isinstance(other, int):
            return self.from_components(self.i_component + other, self.j_component + other)
        return self.from_components(self.i_component + other.i_component, self.j_component + other.j_component)

    def __sub__(self, other: int | Vector2D) -> Self:
        if isinstance(other, int):
            return self.from_components(self.i_component - other, self.j_component - other)
        return self.from_components(self.i_component - other.i_component, self.j_component - other.j_component)

    def __mul__(self, other: int | Vector2D) -> Self:
        if isinstance(other, int):
            return self.from_components(self.i_component * other, self.j_component * other)
        return self.from_components(self.i_component * other.i_component, self.j_component * other.j_component)

    def __floordiv__(self, other: int | Vector2D) -> Self:
        if isinstance(other, int):
            return self.from_components(self.i_component // other, self.j_component // other)
        return self.from_components(self.i_component // other.i_component, self.j_component // other.j_component)

    def __mod__(self, other: int | Vector2D) -> Self:
        if isinstance(other, int):
            return self.from_components(self.i_component % other, self.j_component % other)
        return self.from_components(self.i_component % other.i_component, self.j_component % other.j_component)

    def __and__(self, other: int | Vector2D) -> Self:
        if isinstance(other, int):
            return self.from_components(self.i_component & other, self.j_component & other)
        return self.from_components(self.i_component & other.i_component, self.j_component & other.j_component)

    def __or__(self, other: int | Vector2D) -> Self:
        if isinstance(other, int):
            return self.from_components(self.i_component | other, self.j_component | other)
        return self.from_components(self.i_component | other.i_component, self.j_component | other.j_component)

    def __xor__(self, other: int | Vector2D) -> Self:
        if isinstance(other, int):
            return self.from_components(self.i_component ^ other, self.j_component ^ other)
        return self.from_components(self.i_component ^ other.i_component, self.j_component ^ other.j_component)


@attrs(slots=True, auto_attribs=True, eq=False, frozen=True, hash=False)
class Bound:
    def __contains__(self, element: Bound) -> bool:
        return NotImplemented

    @property
    def points(self) -> Sequence[Point]:
        return NotImplemented

    @property
    def edges(self) -> Sequence[Line]:
        return NotImplemented

    @property
    def left(self) -> int:
        return min(point.x for point in self.points)

    @property
    def right(self) -> int:
        return max(point.x for point in self.points)

    @property
    def bottom(self) -> int:
        return min(point.y for point in self.points)

    @property
    def top(self) -> int:
        return max(point.y for point in self.points)

    def intersects(self, bound: Bound) -> bool:
        return NotImplemented


@attrs(slots=True, auto_attribs=True, eq=False, frozen=True, hash=True)
@default_validator
class Point(ConcreteValidator, KeywordValidator, Vector2D, Bound):
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

    def __str__(self) -> str:
        return f"<{self.x}, {self.y}>"

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

    def __contains__(self, element: Bound) -> bool:
        return all(self == point for point in element.points)

    @property
    def i_component(self) -> int:
        return self.x

    @property
    def j_component(self) -> int:
        return self.y

    @property
    def points(self) -> Sequence[Point]:
        return (self,)

    @property
    def edges(self) -> Sequence[Line]:
        return ()

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

    @classmethod
    @validate(x=IntegerValidator, y=IntegerValidator)
    def validate(cls, x: int, y: int) -> Self:
        return cls(x, y)

    @classmethod
    def from_components(cls, i_component: int, j_component: int) -> Self:
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
        Self
            The point created from the two components.
        """
        return cls(i_component, j_component)

    @classmethod
    def from_vector(cls, vector: Vector2D) -> Self:
        """
        Generates a point from a vector.

        Parameters
        ----------
        vector : Vector2D
            The vector with the i and j components representing the x and y positions of the point, respectively.

        Returns
        -------
        Self
            The point created from the vector.
        """
        return cls(vector.i_component, vector.j_component)

    @classmethod
    def from_qt(cls, point: QPoint | QPointF) -> Self:
        """
        Generates a point from a QPoint for easy conversion.

        Parameters
        ----------
        point : QPoint | QPointF
            To be converted.

        Returns
        -------
        Self
            Of the QPoint represented inside Python.
        """
        if isinstance(point, QPointF):
            return cls(int(point.x()), int(point.y()))
        return cls(point.x(), point.y())

    def evolve(self, *, x: int | None = None, y: int | None = None) -> Self:
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
        Self
            The new evolved point.
        """
        return evolve(self, x=self.x if x is None else x, y=self.y if y is None else y)

    def intersects(self, bound: Bound) -> bool:
        return False

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
class Line(Bound):
    endpoint1: Point
    endpoint2: Point

    def __str__(self) -> str:
        return f"<{self.endpoint1}, {self.endpoint2}>"

    def __contains__(self, element: Bound) -> bool:
        for point in element.points:
            if self.endpoint1 == self.endpoint2 and self.endpoint1 != point:
                return False

            cross_product: int = (point.y - self.endpoint1.y) * (self.endpoint2.x - self.endpoint1.x) - (
                point.x - self.endpoint1.x
            ) * (self.endpoint2.y - self.endpoint1.y)
            if cross_product != 0:
                return False

            dot_product: int = (point.x - self.endpoint1.x) * (self.endpoint2.x - self.endpoint1.x) + (
                point.y - self.endpoint1.y
            ) * (self.endpoint2.y - self.endpoint1.y)
            if dot_product < 0:
                return False

            if dot_product > self.squared_length:
                return False
        return True

    @property
    def points(self) -> Sequence[Point]:
        return (self.endpoint1, self.endpoint2)

    @property
    def edges(self) -> Sequence[Line]:
        return (self,)

    @property
    def squared_length(self) -> int:
        return (self.endpoint2.x - self.endpoint1.x) * (self.endpoint2.x - self.endpoint1.x) + (
            self.endpoint2.y - self.endpoint1.y
        ) * (self.endpoint2.y - self.endpoint1.y)

    def side(self, point: Point) -> int:
        d: int = (point.y - self.endpoint1.y) * (self.endpoint2.x - self.endpoint1.x) - (
            self.endpoint2.y - self.endpoint1.y
        ) * (point.x - self.endpoint1.x)
        return 1 if d > 0 else (-1 if d < 0 else 0)

    def collinear(self, line: Line) -> bool:
        return line.endpoint1 in self and line.endpoint2 in self

    def intersects(self, bound: Bound) -> bool:
        if not isinstance(bound, Line):
            return bound.intersects(self)

        if self.endpoint1 == self.endpoint2:
            return self.endpoint1 == bound.endpoint1 or self.endpoint1 == bound.endpoint2
        if bound.endpoint1 == bound.endpoint2:
            return bound.endpoint1 == self.endpoint1 or bound.endpoint1 == self.endpoint2

        s1: int = self.side(bound.endpoint1)
        s2: int = self.side(bound.endpoint2)

        # Points are collinear
        if s1 == 0 and s2 == 0:
            return (
                bound.endpoint1 in self or bound.endpoint2 in self or self.endpoint1 in bound or self.endpoint2 in bound
            )

        # Not touching and on same side
        if s1 and s1 == s2:
            return False

        s1 = bound.side(self.endpoint1)
        s2 = bound.side(self.endpoint2)

        return not s1 or s1 != s2


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

    width: int = field(validator=ge(0))
    height: int = field(validator=ge(0))
    __names__ = ("__SIZE_VALIDATOR__", "size", "Size", "SIZE")
    __required_validators__ = (NonNegativeIntegerValidator,)

    @property
    def i_component(self) -> int:
        return self.width

    @property
    def j_component(self) -> int:
        return self.height

    def __str__(self) -> str:
        return f"<{self.width, self.height}>"

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
    def validate(cls, width: int, height: int) -> Self:
        return cls(width, height)

    @classmethod
    def from_components(cls, i_component: int, j_component: int) -> Self:
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
        Self
            The size created from the two components.
        """
        return cls(i_component, j_component)

    @classmethod
    def from_vector(cls, vector: Vector2D) -> Self:
        """
        Generates a size from a vector.

        Parameters
        ----------
        vector : Vector2D
            The vector with the i and j components representing the width and height positions of the point,
            respectively.

        Returns
        -------
        Self
            The size created from the vector.
        """
        return cls(vector.i_component, vector.j_component)

    @classmethod
    def from_qt(cls, size: QSize) -> Self:
        """
        Generates a size from a QSize for easy conversion.

        Parameters
        ----------
        size : QSize
            To be converted.

        Returns
        -------
        Self
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


class SimpleBound(Bound):
    def __contains__(self, element: Bound) -> bool:
        return NotImplemented

    @property
    def points(self) -> Sequence[Point]:
        return NotImplemented

    @property
    def edges(self) -> Sequence[Line]:
        return NotImplemented

    def intersects(self, bound: Bound) -> bool:
        if bound.right < self.left or self.right < bound.left or bound.top < self.bottom or self.top < bound.bottom:
            return False
        return any(edge.intersects(bound_edge) for bound_edge in bound.edges for edge in self.edges)


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
@default_validator
class Rect(ConcreteValidator, KeywordValidator, SimpleBound):
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

    def __str__(self) -> str:
        return f"<{self.point, self.size}>"

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

    def __contains__(self, element: Bound) -> bool:
        return all(
            self.point.x <= point.x <= self.point.x + self.size.width
            and self.point.y <= point.y <= self.point.y + self.size.height
            for point in element.points
        )

    @property
    def points(self) -> Sequence[Point]:
        return (self.upper_left_point, self.upper_right_point, self.lower_left_point, self.lower_right_point)

    @property
    def edges(self) -> Sequence[Line]:
        return (self.top_edge, self.bottom_edge, self.left_edge, self.right_edge)

    @property
    def top(self) -> int:
        return max(self.point.y, self.point.y + self.size.height)

    @property
    def top_edge(self) -> Line:
        return Line(Point(self.left, self.top), Point(self.right, self.top))

    @property
    def bottom(self) -> int:
        return min(self.point.y, self.point.y + self.size.height)

    @property
    def bottom_edge(self) -> Line:
        return Line(Point(self.left, self.bottom), Point(self.right, self.bottom))

    @property
    def left(self) -> int:
        return min(self.point.x, self.point.x + self.size.width)

    @property
    def left_edge(self) -> Line:
        return Line(Point(self.left, self.top), Point(self.left, self.bottom))

    @property
    def right(self) -> int:
        return max(self.point.x, self.point.x + self.size.width)

    @property
    def right_edge(self) -> Line:
        return Line(Point(self.right, self.top), Point(self.right, self.bottom))

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

    @classmethod
    @validate(point=Point, size=Size)
    def validate(cls, point: Point, size: Size) -> Self:
        return cls(point, size)

    @classmethod
    def from_points(cls, *points: Point) -> Self:
        min_x: int = min(point.x for point in points)
        min_y: int = min(point.y for point in points)
        max_x: int = max(point.x for point in points)
        max_y: int = max(point.y for point in points)
        return cls(Point(min_x, min_y), Size(max_x - min_x, max_y - min_y))

    @classmethod
    def from_vector(cls, v1: Vector2D, v2: Vector2D) -> Self:
        return cls(Point.from_vector(v1), Size.from_vector(v2))

    def evolve_top(self, top: int) -> Self:
        return self.__class__(Point(self.point.x, top), self.size)

    def evolve_bottom(self, bottom: int) -> Self:
        return self.__class__(self.point, Size(self.size.width, abs(self.point.y - bottom)))

    def evolve_left(self, left: int) -> Self:
        return self.__class__(Point(left, self.point.y), self.size)

    def evolve_right(self, right: int) -> Self:
        return self.__class__(self.point, Size(abs(self.point.x - right), self.size.height))

    def evolve(
        self, *, top: int | None = None, bottom: int | None = None, left: int | None = None, right: int | None = None
    ) -> Self:
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
