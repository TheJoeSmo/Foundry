from __future__ import annotations

from functools import cache
from json import loads
from pathlib import Path
from typing import Iterator

from attr import attrs, field, validators
from pydantic.errors import (
    EnumMemberError,
    MissingError,
    NumberNotGeError,
    NumberNotLeError,
)
from pydantic.validators import int_validator, list_validator
from PySide6.QtGui import QColor

from foundry import data_dir
from foundry.core.Enum import Enum
from foundry.core.file.FilePath import FilePath
from foundry.game.File import ROM
from foundry.smb3parse.constants import BASE_OFFSET, Palette_By_Tileset

PALETTE_GROUPS_PER_OBJECT_SET = 8
ENEMY_PALETTE_GROUPS_PER_OBJECT_SET = 4
PALETTES_PER_PALETTES_GROUP = 4
COLORS_PER_PALETTE = 4

_PRG_SIZE = 0x2000
_PALETTE_PRG_NO = 22
_PALETTE_BASE_ADDRESS = BASE_OFFSET + _PALETTE_PRG_NO * _PRG_SIZE
_PALETTE_OFFSET_LIST = Palette_By_Tileset
_PALETTE_OFFSET_SIZE = 2  # bytes
_PALETTE_FILE_COLOR_OFFSET = 0x18
_PALETTE_FILE_PATH = data_dir / "palette.json"


def _check_in_color_range(inst, attr, value):
    if not 0 <= value <= 0xFF:
        raise ValueError(f"{value} is not inside the range 0-255")
    return value


@attrs(slots=True, frozen=True, eq=True, hash=True)
class Color:
    red: int = field(validator=[validators.instance_of(int), _check_in_color_range])
    green: int = field(validator=[validators.instance_of(int), _check_in_color_range])
    blue: int = field(validator=[validators.instance_of(int), _check_in_color_range])
    alpha: int = field(default=255, validator=[validators.instance_of(int), _check_in_color_range])

    @property
    def qcolor(self) -> QColor:
        return QColor(self.red, self.green, self.blue, self.alpha)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, values) -> Color:
        if "red" not in values:
            MissingError()
        if "green" not in values:
            MissingError()
        if "blue" not in values:
            MissingError()
        red: int = int_validator(values["red"])
        green: int = int_validator(values["green"])
        blue: int = int_validator(values["blue"])
        alpha: int = int_validator(values["alpha"]) if "alpha" in values else 255
        if any(color < 0 for color in [red, green, blue, alpha]):
            raise NumberNotGeError(limit_value=0)
        if any(color > 255 for color in [red, green, blue, alpha]):
            raise NumberNotLeError(limit_value=255)
        return Color(red, green, blue, alpha)


class ColorPaletteType(str, Enum):
    """
    A declaration of the color palettes possible to be created through
    `JSON <https://en.wikipedia.org/wiki/JSON>`_ and
    `Pydantic <https://pydantic-docs.helpmanual.io/>`_.
    """

    default = "DEFAULT"
    colors = "COLORS"
    palette_file = "PALETTE FILE"
    json_file = "JSON FILE"


_DEFAULT_COLOR_PALETTE: None | ColorPalette = None


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class ColorPalette:
    """
    A representation of a series of colors.
    """

    colors: tuple[Color, ...]

    def __getitem__(self, item: int) -> Color:
        return self.colors[item]

    def __iter__(self) -> Iterator[Color]:
        return iter(self.colors)

    def __len__(self) -> int:
        return len(self.colors)

    @property
    def default_color(self) -> Color:
        """
        The class:~`foundry.core.palette.Color` of a color palette to be used when no other color is specified.

        Returns
        -------
        Color
            The default color of this color palette.

        Raises
        ------
        IndexError
            The color palette does not have any colors inside of itself to select.
        """
        try:
            return self[0]
        except IndexError as e:
            raise IndexError("An empty color palette does not have a default color") from e

    @classmethod
    def from_json(cls, path: Path) -> ColorPalette:
        """
        Generates a color palette from a JSON file.

        Parameters
        ----------
        path : Path
            The path to the JSON file.

        Returns
        -------
        ColorPalette
            The color palette that represents the JSON at `path`.
        """
        with open(path, "r") as f:
            data = f.read()
        return cls.validate(loads(data))

    @classmethod
    def from_palette_file(cls, path: Path) -> ColorPalette:
        """
        Generates a color palette from a PAL file.

        Parameters
        ----------
        path : Path
            The path to the PAL file.

        Returns
        -------
        ColorPalette
            The color palette that represents the file at `path`.
        """
        with open(path, "rb") as f:
            data = f.read()
        return ColorPalette(
            tuple(Color(data[i], data[i + 1], data[i + 2]) for i in range(_PALETTE_FILE_COLOR_OFFSET, len(data), 4))
        )

    @classmethod
    def as_default(cls) -> ColorPalette:
        """
        The default NES palette.

        Returns
        -------
        ColorPalette
            The palette that represents the NES palette.
        """
        global _DEFAULT_COLOR_PALETTE
        if _DEFAULT_COLOR_PALETTE is None:
            _DEFAULT_COLOR_PALETTE = cls.from_json(_PALETTE_FILE_PATH)
        return _DEFAULT_COLOR_PALETTE

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate_from_colors(cls, values: dict) -> ColorPalette:
        """
        Generates a color palette from a series of colors.

        Parameters
        ----------
        values : dict
            The values to evaluate.

        Returns
        -------
        ColorPalette
            The color palette that represents the colors provided.
        """
        if "colors" not in values:
            MissingError()
        colors = list_validator(values["colors"])
        return ColorPalette(tuple(Color.validate(c) for c in colors))

    @classmethod
    def validate_from_palette_file(cls, values) -> ColorPalette:
        """
        Generates a color palette from a palette file.

        Parameters
        ----------
        values: dict
            The values to evaluate.

        Returns
        -------
        ColorPalette
            The color palette that represents the palette file.
        """
        if "path" not in values:
            MissingError()
        path = FilePath(values["path"])
        return cls.from_palette_file(path)

    @classmethod
    def validate_from_json_file(cls, values: dict) -> ColorPalette:
        """
        Generates a color palette from a JSON file.

        Parameters
        ----------
        values: dict
            The values to evaluate.

        Returns
        -------
        ColorPalette
            The color palette that represents the JSON file.
        """
        if "path" not in values:
            MissingError()
        path = FilePath(values["path"])
        return cls.from_json(path)

    @classmethod
    def validate_by_type(cls, type_: ColorPaletteType, values: dict) -> ColorPalette:
        if type_ == ColorPaletteType.default:
            return cls.as_default()
        if type_ == ColorPaletteType.colors:
            return cls.validate_from_colors(values)
        if type_ == ColorPaletteType.palette_file:
            return cls.validate_from_palette_file(values)
        if type_ == ColorPaletteType.json_file:
            return cls.validate_from_json_file(values)
        raise NotImplementedError(f"There is no color palette of type {type_}")

    @classmethod
    def validate(cls, values: dict) -> ColorPalette:
        if "type" not in values:
            MissingError()
        type_ = values["type"]
        if not ColorPaletteType.has_value(type_):
            raise EnumMemberError(enum_values=list(ColorPaletteType._value2member_map_))
        return cls.validate_by_type(type_, values)


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
    def colors(self) -> list[Color]:
        """
        A list of :class:~`foundry.core.palette.Colors` that represent this instance.

        Returns
        -------
        list[QColor]
            A list of QColors derived from `color_indexes` and `color_palette`.
        """
        return [self.color_palette.colors[index % len(self.color_palette.colors)] for index in self.color_indexes]

    @property
    def qcolors(self) -> list[QColor]:
        """
        A list of :class:~`foundry.core.palette.Colors` that represent this instance.

        Returns
        -------
        list[QColor]
            A list of QColors derived from `color_indexes` and `color_palette`.
        """
        return [c.qcolor for c in self.colors]

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


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class PaletteGroup:
    """
    A concrete implementation of a hashable and immutable group of palettes.
    """

    palettes: tuple[Palette, ...] = (Palette(), Palette(), Palette(), Palette())

    def __bytes__(self) -> bytes:
        b = bytearray()
        for palette in self.palettes:
            b.extend(bytes(palette))
        return bytes(b)

    def __getitem__(self, item: int) -> Palette:
        return self.palettes[item]

    def __iter__(self) -> Iterator[Palette]:
        return iter(self.palettes)

    @property
    def background_color(self) -> Color:
        return self.palettes[0].colors[0]

    @property
    def background_qcolor(self) -> QColor:
        return self.palettes[0].qcolors[0]

    @classmethod
    def from_rom(cls, address: int) -> PaletteGroup:
        """
        Creates a palette group from an absolute address in ROM.

        Parameters
        ----------
        address : int
            The absolute address into the ROM.

        Returns
        -------
        PaletteGroup
            The palette group that represents the absolute address in ROM.
        """
        return cls(
            tuple(
                Palette.from_rom(address + offset)
                for offset in [COLORS_PER_PALETTE * i for i in range(PALETTES_PER_PALETTES_GROUP)]
            )
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
        Palette
            The PaletteGroup that represents the tileset's palette group at the provided offset.
        """
        offset = get_internal_palette_offset(tileset) + index * PALETTES_PER_PALETTES_GROUP * COLORS_PER_PALETTE
        return cls.from_rom(offset)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, values) -> PaletteGroup:
        if "palettes" not in values:
            raise MissingError()
        palettes = list_validator(values["palettes"])
        return cls(tuple(Palette.validate(pal) for pal in palettes))


@cache
def get_internal_palette_offset(tileset: int) -> int:
    """
    Provides the absolute internal point of the palette group offset from ROM.

    Parameters
    ----------
    tileset : int
        The tileset to find the absolute internal point of.

    Returns
    -------
    int
        The absolute internal point of the tileset's palette group.
    """
    return _PALETTE_BASE_ADDRESS + ROM().little_endian(_PALETTE_OFFSET_LIST + (tileset * _PALETTE_OFFSET_SIZE))
