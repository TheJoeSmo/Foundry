from __future__ import annotations

from collections.abc import Iterator
from enum import Enum
from functools import cached_property
from typing import Protocol, Sequence

from attr import attrs
from pydantic import BaseModel
from PySide6.QtGui import QColor

from foundry.core.palette import COLORS_PER_PALETTE
from foundry.core.palette.ColorPalette import ColorPalette
from foundry.game.File import ROM


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=False)
class Palette:
    """
    A representation of a series of colors that are indexable.

    Returns
    -------
    color_indexes: tuple[int, ...]
        A series of indexes into the `color_palette`, which represent the respective colors.
    color_palette: ColorPalette
        A series of indexable colors.
    """

    color_indexes: tuple[int, ...] = (0, 0, 0, 0)
    color_palette: ColorPalette = ColorPalette.as_default()

    def __bytes__(self) -> bytes:
        return bytes(i & 0xFF for i in self.color_indexes)

    def __getitem__(self, item: int) -> int:
        return self.color_indexes[item]

    def __iter__(self) -> Iterator[int]:
        return iter(self.color_indexes)

    def __hash__(self) -> int:
        return hash(self.color_indexes)

    @property
    def colors(self) -> Sequence[QColor]:
        """
        A sequence of QColors that represent this instance.

        Returns
        -------
        Sequence[QColor]
            A sequence of QColors derived from `color_indexes` and `color_palette`.
        """
        return [
            self.color_palette.colors[index % len(self.color_palette.colors)].qcolor for index in self.color_indexes
        ]

    @classmethod
    def from_rom(cls, address: int) -> Palette:
        """
        Creates a palette from an absolute address in the file.

        Parameters
        ----------
        address : int
            The absolute address into the file.

        Returns
        -------
        Palette
            The palette that represents the absolute address in ROM.
        """
        return cls(tuple(int(i) for i in ROM().read(address, COLORS_PER_PALETTE)))


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
    def palette(self) -> Palette:
        ...


class PydanticColorsPalette(PydanticPalette):
    """
    A palette which generates itself from a series of indexes into the color palette.

    Attributes
    ----------
    color_indexes: list[int]
        A list of indexes into the color palette colors.
    color_palette: ColorPalette
        A color palette generator which provides the colors which are indexed.
    """

    color_indexes: list[int]
    color_palette: ColorPalette = ColorPalette.as_default()

    @property
    def color_palette_(self) -> ColorPalette:
        """
        A simple wrapper around the true color palette to provide correct type hints.

        Returns
        -------
        ColorPalette
            The color palette that is supplied.
        """
        return self.color_palette

    @cached_property
    def palette(self) -> Palette:
        """
        Provides the representation of a palette from the Pydantic version.

        Returns
        -------
        Protocol
            The corresponding palette.
        """
        return Palette(tuple(self.color_indexes), self.color_palette)


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
    def palette(self) -> Palette:
        """
        Provides the representation of a palette from the ROM.

        Returns
        -------
        Protocol
            The corresponding palette.
        """
        return Palette.from_rom(self.palette_address)


class PaletteCreator(BaseModel):
    """
    A generator for a :class:`~foundry.core.palette.Palette.Palette`.
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
