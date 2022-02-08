from abc import ABC, abstractmethod
from typing import Protocol, Type, TypeVar

from attr import attrs
from pydantic import BaseModel, validator


class SizeProtocol(Protocol):
    """
    A two dimensional representation of a size of a given object.

    Attributes
    ----------
    width: int
        The width of the object being represented.
    height: int
        The height of the object being represented.
    """

    width: int
    height: int


class HashableSizeProtocol(SizeProtocol, Protocol):
    def __hash__(self) -> int:
        ...


_T = TypeVar("_T", bound="AbstractSize")


class AbstractSize(ABC):
    width: int
    height: int

    @classmethod
    @abstractmethod
    def from_values(cls: Type[_T], width: int, height: int) -> _T:
        """
        A generalized way to create itself from a width and height.

        Returns
        -------
        AbstractSize
            The created size from the width and height.
        """
        ...

    @classmethod
    def from_size(cls: Type[_T], size: SizeProtocol) -> _T:
        """
        Generates a size from a size protocol.

        Parameters
        ----------
        size : SizeProtocol
            The size protocol to be mapped to this size.

        Returns
        -------
        _T
            The size converted to this type.
        """
        return cls.from_values(size.width, size.height)

    def __lt__(self, other: SizeProtocol):
        return self.width * self.height < other.width * other.height

    def __le__(self, other: SizeProtocol):
        return self.width * self.height <= other.width * other.height

    def __gt__(self, other: SizeProtocol):
        return self.width * self.height > other.width * other.height

    def __ge__(self, other: SizeProtocol):
        return self.width * self.height >= other.width * other.height

    def __invert__(self: _T) -> _T:
        return self.from_values(~self.width, ~self.height)

    def __neg__(self: _T) -> _T:
        return self.from_values(~self.width, ~self.height)

    def __lshift__(self: _T, other: int) -> _T:
        return self.from_values(self.width << other, self.height << other)

    def __rshift__(self: _T, other: int) -> _T:
        return self.from_values(self.width >> other, self.height >> other)

    def __pow__(self: _T, other: int) -> _T:
        return self.from_values(self.width ** other, self.height ** other)

    def __add__(self: _T, other: SizeProtocol) -> _T:
        return self.from_values(self.width + other.width, self.height + other.height)

    def __sub__(self: _T, other: SizeProtocol) -> _T:
        return self.from_values(self.width - other.width, self.height - other.height)

    def __mul__(self: _T, other: SizeProtocol) -> _T:
        return self.from_values(self.width * other.width, self.height * other.height)

    def __floordiv__(self: _T, other: SizeProtocol) -> _T:
        return self.from_values(self.width // other.width, self.height // other.height)

    def __mod__(self: _T, other: SizeProtocol) -> _T:
        return self.from_values(self.width % other.width, self.height % other.height)

    def __and__(self: _T, other: SizeProtocol) -> _T:
        return self.from_values(self.width & other.width, self.height & other.height)

    def __or__(self: _T, other: SizeProtocol) -> _T:
        return self.from_values(self.width | other.width, self.height | other.height)

    def __xor__(self: _T, other: SizeProtocol) -> _T:
        return self.from_values(self.width ^ other.width, self.height ^ other.height)


_MT = TypeVar("_MT", bound="MutableSize")


@attrs(slots=True, auto_attribs=True, eq=True)
class MutableSize(AbstractSize):
    """
    A two dimensional representation of a size, that uses ``attrs`` to create a basic
    implementation.

    Attributes
    ----------
    width: int
        The width of the object being represented.
    height: int
        The height of the object being represented.
    """

    width: int
    height: int

    @classmethod
    def from_values(cls: Type[_MT], width: int, height: int) -> _MT:
        return cls(width, height)


_IT = TypeVar("_IT", bound="Size")


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class Size(AbstractSize):
    """
    A two dimensional representation of a size, that uses ``attrs`` to create a basic
    implementation.

    Attributes
    ----------
    width: int
        The width of the object being represented.
    height: int
        The height of the object being represented.
    """

    width: int
    height: int

    @classmethod
    def from_values(cls: Type[_IT], width: int, height: int) -> _IT:
        return cls(width, height)


class PydanticSize(BaseModel):
    width: int
    height: int

    @validator("width", "height", allow_reuse=True)
    def check_size_range(cls, v):
        if not v > 0:
            raise ValueError(f"{v} must be one or greater")
        return v

    @property
    def size(self) -> SizeProtocol:
        return Size(self.width, self.height)
