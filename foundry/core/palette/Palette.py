from abc import ABC, abstractmethod
from typing import Protocol, Sequence, Type, TypeVar

from attr import attrs
from PySide6.QtGui import QColor

from foundry.core.palette import COLORS_PER_PALETTE, NESPalette
from foundry.game.File import ROM


class PaletteProtocol(Protocol):
    color_indexes: Sequence[int]

    def __bytes__(self) -> bytes:
        ...

    def __getitem__(self, item: int) -> int:
        ...

    @property
    def colors(self) -> Sequence[QColor]:
        ...


class MutablePaletteProtocol(PaletteProtocol, Protocol):
    def __setitem__(self, key: int, value: int):
        ...


class HashablePaletteProtocol(PaletteProtocol, Protocol):
    def __hash__(self) -> int:
        ...


_T = TypeVar("_T", bound="AbstractPalette")


class AbstractPalette(ABC):
    """
    An abstract implementation of the primary methods of a Palette, regardless of color_indexes.
    """

    color_indexes: Sequence[int]

    def __bytes__(self) -> bytes:
        return bytes([i & 0xFF for i in self.color_indexes])

    def __getitem__(self, item: int) -> int:
        return self.color_indexes[item]

    @property
    def colors(self) -> Sequence[QColor]:
        return [NESPalette[c & 0x3F] for c in self.color_indexes]

    @classmethod
    @abstractmethod
    def from_values(cls: Type[_T], *values: int) -> _T:
        """
        A generalized way to create itself from a series of values.

        Returns
        -------
        AbstractPalette
            The created palette from the series.
        """
        ...

    @classmethod
    def from_palette(cls: Type[_T], palette: PaletteProtocol) -> _T:
        """
        Generates a AbstractPalette of this type from another PaletteProtocol.

        Parameters
        ----------
        palette : PaletteProtocol
            The palette to be converted to this type.

        Returns
        -------
        AbstractPalette
            A palette that is equal to the original palette.
        """
        return cls.from_values(*palette.color_indexes)

    @classmethod
    def as_empty(cls: Type[_T]) -> _T:
        """
        Makes an empty palette of default values.

        Returns
        -------
        AbstractPalette
            A palette filled with default values.
        """
        return cls.from_values(0, 0, 0, 0)

    @classmethod
    def from_rom(cls: Type[_T], address: int) -> _T:
        """
        Creates a palette from an absolute address in ROM.

        Parameters
        ----------
        address : int
            The absolute address into the ROM.

        Returns
        -------
        AbstractPalette
            The palette that represents the absolute address in ROM.
        """
        return cls.from_values(*tuple(int(i) for i in ROM().read(address, COLORS_PER_PALETTE)))


_MT = TypeVar("_MT", bound="MutablePalette")


@attrs(slots=True, auto_attribs=True, eq=True)
class MutablePalette(AbstractPalette):
    color_indexes: list[int]

    def __setitem__(self, key: int, value: int):
        self.color_indexes[key] = value

    @classmethod
    def from_values(cls: Type[_MT], *values: int) -> _MT:
        return cls(list(values))


_PT = TypeVar("_PT", bound="Palette")


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class Palette(AbstractPalette):
    color_indexes: tuple[int, ...]

    @classmethod
    def from_values(cls: Type[_PT], *values: int) -> _PT:
        return cls(values)
