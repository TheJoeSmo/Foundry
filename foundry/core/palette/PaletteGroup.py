from abc import ABC, abstractmethod
from typing import ClassVar, Protocol, Sequence, Type, TypeVar

from attr import attrs
from pydantic import BaseModel
from PySide6.QtGui import QColor

from foundry.core.palette import COLORS_PER_PALETTE, PALETTES_PER_PALETTES_GROUP
from foundry.core.palette.Palette import (
    AbstractPalette,
    HashablePaletteProtocol,
    MutablePalette,
    MutablePaletteProtocol,
    Palette,
    PaletteCreator,
    PaletteProtocol,
    PydanticPaletteProtocol,
)
from foundry.core.palette.util import get_internal_palette_offset


class PaletteGroupProtocol(Protocol):
    """
    A representation of a group of palettes.
    """

    palettes: Sequence[PaletteProtocol]

    def __bytes__(self) -> bytes:
        ...

    def __getitem__(self, item: int) -> PaletteProtocol:
        ...

    @property
    def background_color(self) -> QColor:
        ...


class MutablePaletteGroupProtocol(PaletteGroupProtocol, Protocol):
    """
    A mutable representation of a group of palettes.
    """

    def __setitem__(self, key: int, value: PaletteProtocol):
        ...


class HashablePaletteGroupProtocol(PaletteGroupProtocol, Protocol):
    """
    A hashable and immutable representation of a group of palettes.
    """

    def __hash__(self) -> int:
        ...


_T = TypeVar("_T", bound="AbstractPaletteGroup")


class AbstractPaletteGroup(ABC):
    """
    A partial implementation of a palette group that implements the critical parts of a palette group
    independent of its mutability or ability to be hashed.
    """

    palettes: Sequence[PaletteProtocol]

    PALETTE_TYPE: ClassVar[Type[AbstractPalette]] = AbstractPalette

    def __bytes__(self) -> bytes:
        b = bytearray()
        for palette in self.palettes:
            b.extend(bytes(palette))
        return bytes(b)

    def __getitem__(self, item: int) -> PaletteProtocol:
        return self.palettes[item]

    @property
    def background_color(self) -> QColor:
        return self.palettes[0].colors[0]

    @classmethod
    @abstractmethod
    def from_values(cls: Type[_T], *values: PaletteProtocol) -> _T:
        """
        A generalized way to create itself from a series of values.

        Returns
        -------
        AbstractPaletteGroup
            The created palette group from the series.
        """
        ...

    @classmethod
    def from_palette_group(cls: Type[_T], palette_group: PaletteGroupProtocol) -> _T:
        """
        Generates a AbstractPaletteGroup of this type from another PaletteGroupProtocol.

        Parameters
        ----------
        palette_group : PaletteGroupProtocol
            The palette to be converted to this type.

        Returns
        -------
        AbstractPaletteGroup
            A palette group that is equal to the original palette group.
        """
        return cls.from_values(*palette_group.palettes)

    @classmethod
    def as_empty(cls: Type[_T]) -> _T:
        """
        Makes an empty palette group of default values.

        Returns
        -------
        AbstractPaletteGroup
            The palette group filled with default values.
        """
        return cls.from_values(*[cls.PALETTE_TYPE.as_empty() for _ in range(PALETTES_PER_PALETTES_GROUP)])

    @classmethod
    def from_rom(cls: Type[_T], address: int) -> _T:
        """
        Creates a palette group from an absolute address in ROM.

        Parameters
        ----------
        address : int
            The absolute address into the ROM.

        Returns
        -------
        AbstractPaletteGroup
            The palette group that represents the absolute address in ROM.
        """
        return cls.from_values(
            *[
                cls.PALETTE_TYPE.from_rom(address + offset)
                for offset in [COLORS_PER_PALETTE * i for i in range(PALETTES_PER_PALETTES_GROUP)]
            ]
        )

    @classmethod
    def from_tileset(cls, tileset: int, index: int):
        """
        Loads a palette group from a tileset with a given index.

        Parameters
        ----------
        tileset : int
            The index of the tileset.
        index : int
            The index of the palette group inside the tileset.

        Returns
        -------
        MutablePaletteGroup
            The PaletteGroup that represents the tileset's palette group at the provided offset.
        """
        offset = get_internal_palette_offset(tileset) + index * PALETTES_PER_PALETTES_GROUP * COLORS_PER_PALETTE
        return cls.from_rom(offset)


_MT = TypeVar("_MT", bound="MutablePaletteGroup")


@attrs(slots=True, auto_attribs=True, eq=True)
class MutablePaletteGroup(AbstractPaletteGroup):
    """
    A concrete implementation of a mutable group of palettes.
    """

    palettes: list[MutablePaletteProtocol]

    PALETTE_TYPE: ClassVar[Type[MutablePalette]] = MutablePalette

    def __setitem__(self, key: int, value: MutablePaletteProtocol):
        self.palettes[key] = value

    @classmethod
    def from_values(cls: Type[_MT], *values: PaletteProtocol) -> _MT:
        return cls([cls.PALETTE_TYPE.from_palette(palette) for palette in values])


_PT = TypeVar("_PT", bound="PaletteGroup")


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class PaletteGroup(AbstractPaletteGroup):
    """
    A concrete implementation of a hashable and immutable group of palettes.
    """

    palettes: tuple[HashablePaletteProtocol]

    PALETTE_TYPE: ClassVar[Type[Palette]] = Palette

    @classmethod
    def from_values(cls: Type[_PT], *values: PaletteProtocol) -> _PT:
        return cls(tuple(cls.PALETTE_TYPE.from_palette(palette) for palette in values))


class PydanticPaletteGroup(BaseModel):
    """
    A generic representation of :class:`~foundry.core.palette.PaletteGroup.PaletteGroup`.

    Attributes
    ----------
    palettes: list[PaletteCreator]
        The palettes that compose the palette group.
    """

    palettes: list[PaletteCreator]

    @property
    def palette_protocols(self) -> list[PydanticPaletteProtocol]:
        return self.palettes  # type: ignore

    @property
    def palette_group(self) -> PaletteGroupProtocol:
        return PaletteGroup.from_values(*[p.palette for p in self.palette_protocols])
