from abc import ABC, abstractmethod
from collections.abc import Sequence
from enum import Enum
from functools import cached_property
from typing import Protocol, TypeVar

from attr import attrs
from pydantic import BaseModel
from PySide6.QtGui import QColor

from foundry.core.palette import COLORS_PER_PALETTE
from foundry.core.palette.ColorPalette import (
    ColorPaletteCreator,
    ColorPaletteProtocol,
    PydanticColorPaletteProtocol,
)
from foundry.game.File import ROM


class PaletteProtocol(Protocol):
    color_indexes: Sequence[int]
    color_palette: ColorPaletteProtocol

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
    color_palette: ColorPaletteProtocol

    def __bytes__(self) -> bytes:
        return bytes(i & 0xFF for i in self.color_indexes)

    def __getitem__(self, item: int) -> int:
        return self.color_indexes[item]

    @property
    def colors(self) -> Sequence[QColor]:
        return [
            self.color_palette.colors[index % len(self.color_palette.colors)].qcolor for index in self.color_indexes
        ]

    @classmethod
    @abstractmethod
    def from_values(
        cls: type[_T], color_indexes: Sequence[int], color_palette: ColorPaletteProtocol | None = None
    ) -> _T:
        """
        A generalized way to create itself from a series of values.

        Returns
        -------
        AbstractPalette
            The created palette from the series.
        """
        ...

    @classmethod
    def from_palette(cls: type[_T], palette: PaletteProtocol) -> _T:
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
        return cls.from_values(palette.color_indexes, palette.color_palette)

    @classmethod
    def as_empty(cls: type[_T]) -> _T:
        """
        Makes an empty palette of default values.

        Returns
        -------
        AbstractPalette
            A palette filled with default values.
        """
        return cls.from_values([0, 0, 0, 0])

    @classmethod
    def from_rom(cls: type[_T], address: int) -> _T:
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
        return cls.from_values(tuple(int(i) for i in ROM().read(address, COLORS_PER_PALETTE)))


_MT = TypeVar("_MT", bound="MutablePalette")


@attrs(slots=True, auto_attribs=True, eq=True)
class MutablePalette(AbstractPalette):
    color_indexes: list[int]
    color_palette: ColorPaletteProtocol = ColorPaletteCreator.as_default().color_palette

    def __setitem__(self, key: int, value: int):
        self.color_indexes[key] = value

    @classmethod
    def from_values(
        cls: type[_MT], color_indexes: Sequence[int], color_palette: ColorPaletteProtocol | None = None
    ) -> _MT:
        if color_palette is None:
            return cls(list(color_indexes))
        else:
            return cls(list(color_indexes), color_palette)


_PT = TypeVar("_PT", bound="Palette")


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class Palette(AbstractPalette):
    color_indexes: tuple[int, ...]
    color_palette: ColorPaletteProtocol = ColorPaletteCreator.as_default().color_palette

    @classmethod
    def from_values(
        cls: type[_PT], color_indexes: Sequence[int], color_palette: ColorPaletteProtocol | None = None
    ) -> _PT:
        if color_palette is None:
            return cls(tuple(color_indexes))
        else:
            return cls(tuple(color_indexes), color_palette)


class PaletteType(str, Enum):
    """
    A declaration of the palettes possible to be created through
    `JSON <https://en.wikipedia.org/wiki/JSON>`_ and
    `Pydantic <https://pydantic-docs.helpmanual.io/>`_.
    """

    from_colors = "COLORS"
    from_rom_address = "ROM ADDRESS"

    @classmethod
    def has_value(cls, value):
        """
        A convenience method to quickly determine if a value is a valid enumeration.

        Parameters
        ----------
        value : str
            The value to check against the enumeration.

        Returns
        -------
        bool
            If the value is inside the enumeration.
        """

        return value in cls._value2member_map_


class PydanticPalette(BaseModel):
    """
    A generic representation of :class:`~foundry.core.palette.Palette.Palette`.

    Attributes
    ----------
    type: PaletteType
        How the Palette should be loaded.
    """

    type: PaletteType

    class Config:
        # Allow storing the enum as a string
        use_enum_values = True

        # Enable cached property to be ignored by Pydantic
        arbitrary_types_allowed = True
        keep_untouched = (cached_property,)


class PydanticPaletteProtocol(Protocol):
    """
    A Pydantic palette that can convert to a regular palette.
    """

    @cached_property
    def palette(self) -> PaletteProtocol:
        ...


class PydanticColorsPalette(PydanticPalette):
    """
    A palette which generates itself from a series of indexes into the color palette.

    Attributes
    ----------
    color_indexes: list[int]
        A list of indexes into the color palette colors.
    color_palette: ColorPaletteCreator
        A color palette generator which provides the colors which are indexed.
    """

    color_indexes: list[int]
    color_palette: ColorPaletteCreator = ColorPaletteCreator(type="DEFAULT")

    @property
    def color_palette_(self) -> PydanticColorPaletteProtocol:
        """
        A simple wrapper around the true color palette to provide correct type hints.

        Returns
        -------
        ColorPaletteProtocol
            The color palette that is supplied.
        """
        return self.color_palette  # type: ignore

    @cached_property
    def palette(self) -> PaletteProtocol:
        """
        Provides the representation of a palette from the Pydantic version.

        Returns
        -------
        PaletteProtocol
            The corresponding palette.
        """
        return Palette.from_values(self.color_indexes, self.color_palette_.color_palette)


class PydanticROMAddressPalettePalette(PydanticPalette):
    """
    A palette which generates itself from an address in the ROM and the default color palette.

    Attributes
    ----------
    palette_address: int
        The index into the ROM to generate the palette from.
    """

    palette_address: int

    @cached_property
    def palette(self) -> PaletteProtocol:
        """
        Provides the representation of a palette from the ROM.

        Returns
        -------
        PaletteProtocol
            The corresponding palette.
        """
        return Palette.from_rom(self.palette_address)


class PaletteCreator(BaseModel):
    """
    A generator for a :class:`~foundry.core.palette.Palette.PaletteProtocol`.
    Creates the palette dynamically from its type attribute to provide it additional information.
    """

    def __init_subclass__(cls, **kwargs) -> None:
        return super().__init_subclass__(**kwargs)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def generate_palette(cls, v: dict) -> PydanticPaletteProtocol:
        """
        The constructor for each specific palette.

        Parameters
        ----------
        v : dict
            The dictionary to create the palette from.

        Returns
        -------
        PydanticPaletteProtocol
            The created palette as defined by `v["type"]`

        Raises
        ------
        NotImplementedError
            If the constructor does not have a valid constructor for `v["type"]`.
        """

        type_ = PaletteType(v["type"])
        if type_ == PaletteType.from_colors:
            return PydanticColorsPalette(**v)
        if type_ == PaletteType.from_rom_address:
            return PydanticROMAddressPalettePalette(**v)
        raise NotImplementedError(f"There is no palette of type {type_}")

    @classmethod
    def validate(cls, v) -> PydanticPaletteProtocol:
        """
        Validates that the provided object is a valid palette.

        Parameters
        ----------
        v : dict
            The dictionary to create the palette from.

        Returns
        -------
        PydanticPaletteProtocol
            If validated, a palette will be created in accordance to `generate_palette`.

        Raises
        ------
        TypeError
            If a dictionary is not provided.
        TypeError
            If the dictionary does not contain the key `"type"`.
        TypeError
            If the type provided is not inside :class:`~foundry.core.palette.Color.PaletteType`.
        """
        if not isinstance(v, dict):
            raise TypeError("Dictionary required")
        if "type" not in v:
            raise TypeError("Must have a type")
        if not PaletteType.has_value(type_ := v["type"]):
            raise TypeError(f"{type_} is not a valid layout type")
        return cls.generate_palette(v)
