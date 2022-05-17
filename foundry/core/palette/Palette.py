from __future__ import annotations

from collections.abc import Iterator
from typing import Sequence

from attr import attrs
from pydantic.errors import (
    EnumMemberError,
    MissingError,
    NumberNotGeError,
    NumberNotLeError,
)
from pydantic.validators import int_validator, list_validator
from PySide6.QtGui import QColor

from foundry.core.Enum import Enum
from foundry.core.palette import COLORS_PER_PALETTE
from foundry.core.palette.ColorPalette import ColorPalette
from foundry.game.File import ROM


class PaletteType(str, Enum):
    """
    A declaration of the palettes possible to be created through
    `JSON <https://en.wikipedia.org/wiki/JSON>`_ and
    `Pydantic <https://pydantic-docs.helpmanual.io/>`_.
    """

    from_colors = "COLORS"
    from_rom_address = "ROM ADDRESS"


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

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate_from_colors(cls, values: dict) -> Palette:
        """
        Validates a Palette from a series of colors and a color palette.

        Parameters
        ----------
        values : dict
            A dictionary that contains the values to be validated.  A valid entry
            must contain a field `color_indexes`, which contains a series of integers
            that are valid indexes into `color_palette`.  An optional entry is the
            `color_palette`, which is a class:~`foundry.core.palette.ColorPalette.ColorPalette`
            that will override the default entry.

        Returns
        -------
        Palette
            The palette that represents the values provided.

        Raises
        ------
        MissingError
            The field `color_indexes` is not present inside `values`.
        ListError
            The field `color_indexes` is not a list.
        IntegerError
            Any of the values of `color_indexes` is not an integer.
        NumberNotGeError
            Any of the values of `color_indexes` is not positive.
        NumberNotLeError
            Any of the values of `color_indexes` exceed the length of `color_palette`.
        """
        if "color_indexes" not in values:
            MissingError()
        indexes = list_validator(values["color_indexes"])
        if "color_palette" in values:
            color_palette = ColorPalette.validate(values["color_palette"])
        else:
            color_palette = ColorPalette.as_default()
        color_indexes = []
        for value in indexes:
            index = int_validator(value)
            if index < 0:
                raise NumberNotGeError(limit_value=0)
            if index > len(color_palette):
                raise NumberNotLeError(limit_value=len(color_palette))
            color_indexes.append(index)
        return cls(tuple(color_indexes), color_palette)

    @classmethod
    def validate_from_rom(cls, values: dict) -> Palette:
        """
        Validates a Palette from an address into the ROM.

        Parameters
        ----------
        values : dict
            A dictionary that contains the values to be validated.  A valid entry
            must contain `palette_address`, which is a valid address into the ROM.

        Returns
        -------
        Palette
            The palette that represents the values provided.

        Raises
        ------
        MissingError
            The field `palette_address` is not present inside `values`.
        IntegerError
            `palette_address` is not an integer.
        """
        if "palette_address" not in values:
            MissingError()
        palette_address = int_validator(values["palette_address"])
        return cls.from_rom(palette_address)

    @classmethod
    def validate_by_type(cls, type_: PaletteType, values: dict) -> Palette:
        if type_ == PaletteType.from_colors:
            return cls.validate_from_colors(values)
        if type_ == PaletteType.from_rom_address:
            return cls.validate_from_rom(values)
        raise NotImplementedError(f"There is no palette of type {type_}")

    @classmethod
    def validate(cls, values) -> Palette:
        if "type" not in values:
            MissingError()
        type_ = values["type"]
        if not PaletteType.has_value(type_):
            raise EnumMemberError(enum_values=list(PaletteType._value2member_map_))
        return cls.validate_by_type(type_, values)
