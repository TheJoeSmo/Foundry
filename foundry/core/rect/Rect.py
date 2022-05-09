from abc import ABC, abstractmethod
from typing import Protocol, Type, TypeVar

from attr import attrs
from pydantic import BaseModel

from foundry.core.point.Point import (
    HashablePointProtocol,
    MutablePoint,
    Point,
    PointProtocol,
    PydanticPoint,
)
from foundry.core.size.Size import (
    HashableSizeProtocol,
    MutableSize,
    PydanticSize,
    Size,
    SizeProtocol,
)


class RectProtocol(Protocol):
    """
    A two dimensional representation of a box for a given object.

    Attributes
    ----------
    point: PointProtocol
        The upper left corner of the rect.
    size: SizeProtocol
        The size of the box.
    """

    point: PointProtocol
    size: SizeProtocol


class HashableRectProtocol(RectProtocol, Protocol):
    def __hash__(self) -> int:
        ...


_T = TypeVar("_T", bound="AbstractRect")


class AbstractRect(ABC):
    point: PointProtocol
    size: SizeProtocol

    @classmethod
    @abstractmethod
    def from_values(cls: Type[_T], point: PointProtocol, size: SizeProtocol) -> _T:
        """
        A generalized way to create itself from a point and size.

        Returns
        -------
        AbstractRect
            The created rect from the point and size.
        """
        ...

    @classmethod
    def from_rect(cls: Type[_T], rect: RectProtocol) -> _T:
        """
        Generates a rect from a rect protocol.

        Parameters
        ----------
        rect : RectProtocol
            The rect protocol to be mapped to this rect.

        Returns
        -------
        _T
            The rect converted to this type.
        """
        return cls.from_values(rect.point, rect.size)


_MT = TypeVar("_MT", bound="MutableRect")


@attrs(slots=True, auto_attribs=True, eq=True)
class MutableRect(AbstractRect):
    """
    A two dimensional representation of a box, that uses ``attrs`` to create a basic
    implementation.

    Attributes
    ----------
    point: PointProtocol
        The upper left corner of the rect.
    size: SizeProtocol
        The size of the box.
    """

    point: PointProtocol
    size: SizeProtocol

    @classmethod
    def from_values(cls: Type[_MT], point: PointProtocol, size: SizeProtocol) -> _MT:
        return cls(MutablePoint.from_point(point), MutableSize.from_size(size))


_IT = TypeVar("_IT", bound="Rect")


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class Rect(AbstractRect):
    """
    A two dimensional representation of a box, that uses ``attrs`` to create a basic
    implementation.

    Attributes
    ----------
    point: HashablePointProtocol
        The upper left corner of the rect.
    size: HashableSizeProtocol
        The size of the box.
    """

    point: HashablePointProtocol
    size: HashableSizeProtocol

    @classmethod
    def from_values(cls: Type[_IT], point: PointProtocol, size: SizeProtocol) -> _IT:
        return cls(Point.from_point(point), Size.from_size(size))


class PydanticRect(BaseModel):
    point: PydanticPoint
    size: PydanticSize

    @property
    def rect(self) -> RectProtocol:
        return Rect(self.point.point, self.size.size)
