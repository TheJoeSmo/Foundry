from __future__ import annotations

from json import loads
from pathlib import Path

from attr import attrs
from pydantic.errors import EnumMemberError, MissingError
from pydantic.validators import list_validator

from foundry.core.Enum import Enum
from foundry.core.file.FilePath import FilePath
from foundry.core.palette import PALETTE_FILE_COLOR_OFFSET, PALETTE_FILE_PATH
from foundry.core.palette.Color import Color


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
            tuple(Color(data[i], data[i + 1], data[i + 2]) for i in range(PALETTE_FILE_COLOR_OFFSET, len(data), 4))
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
            _DEFAULT_COLOR_PALETTE = cls.from_json(PALETTE_FILE_PATH)
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
