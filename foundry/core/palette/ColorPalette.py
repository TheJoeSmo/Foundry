from collections.abc import Sequence
from enum import Enum
from functools import cached_property
from json import loads
from pathlib import Path
from typing import Protocol

from attr import attrs
from pydantic import BaseModel, FilePath

from foundry.core.palette import PALETTE_FILE_COLOR_OFFSET, PALETTE_FILE_PATH
from foundry.core.palette.Color import Color, ColorProtocol, PydanticColor


class ColorPaletteProtocol(Protocol):
    colors: Sequence[ColorProtocol]


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class ColorPalette:
    """
    A representation of a series of colors.
    """

    colors: tuple[ColorProtocol, ...]


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


class PydanticColorPalette(BaseModel):
    """
    A generic representation of :class:`~foundry.core.palette.ColorPalette.ColorPalette`.

    Attributes
    ----------
    type: ColorPaletteType
        How the ColorPalette should be loaded.
    """

    type: ColorPaletteType

    class Config:
        # Allow storing the enum as a string
        use_enum_values = True

        # Enable cached property to be ignored by Pydantic
        arbitrary_types_allowed = True
        keep_untouched = (cached_property,)


class PydanticColorPaletteProtocol(Protocol):
    """
    A Pydantic color palette that can convert to a regular color palette.
    """

    @cached_property
    def color_palette(self) -> ColorPaletteProtocol:
        ...


class PydanticColorsColorPalette(PydanticColorPalette):
    """
    A color palette which generates itself from a series of colors.

    Attributes
    ----------
    colors: list[PydanticColor]
        A list of colors that compose the color palette.
    """

    colors: list[PydanticColor]

    @cached_property
    def color_palette(self) -> ColorPaletteProtocol:
        """
        Provides the representation of a color palette from the Pydantic version.

        Returns
        -------
        ColorPaletteProtocol
            The corresponding color palette.
        """
        return ColorPalette(tuple(color.color for color in self.colors))


def palette_file_to_color_palette(path: Path) -> ColorPaletteProtocol:
    """
    Generates a color palette from a palette file.

    Parameters
    ----------
    path : Path
        The path to the palette file.

    Returns
    -------
    ColorPaletteProtocol
        The color palette that represents the palette file.
    """
    with open(path, "rb") as f:
        data = f.read()
    return ColorPalette(
        tuple(Color(data[i], data[i + 1], data[i + 2]) for i in range(PALETTE_FILE_COLOR_OFFSET, len(data), 4))
    )


class PydanticPaletteFileColorPalette(PydanticColorPalette):
    """
    A color palette which generates itself from another file.

    Attributes
    ----------
    path: FilePath
        A palette file to be converted to a color palette.
    """

    path: FilePath

    @cached_property
    def color_palette(self) -> ColorPaletteProtocol:
        """
        Provides the representation of a color palette from the Pydantic version.

        Returns
        -------
        ColorPaletteProtocol
            The corresponding color palette.
        """
        return palette_file_to_color_palette(self.path)


def json_file_to_color_palette(path: Path) -> ColorPaletteProtocol:
    """
    Generates a color palette from a JSON file.

    Parameters
    ----------
    path : Path
        The path to the JSON file.

    Returns
    -------
    ColorPaletteProtocol
        The color palette that represents the JSON file.
    """
    with open(path) as f:
        return ColorPaletteCreator.generate_color_palette(loads(f.read())).color_palette


class PydanticJSONFileColorPalette(PydanticColorPalette):
    """
    A color palette which generates itself from another file.

    Attributes
    ----------
    path: FilePath
        A JSON file to be converted to a color palette.
    """

    path: FilePath

    @cached_property
    def color_palette(self) -> ColorPaletteProtocol:
        """
        Provides the representation of a color palette from the Pydantic version.

        Returns
        -------
        ColorPaletteProtocol
            The corresponding color palette.
        """
        return json_file_to_color_palette(self.path)


class PydanticDefaultColorPalette(PydanticColorPalette):
    """
    A color palette which represents the NES colors inside the game.
    """

    @cached_property
    def color_palette(self) -> ColorPaletteProtocol:
        """
        Provides the representation of a color palette from the Pydantic version.

        Returns
        -------
        ColorPaletteProtocol
            The corresponding color palette.
        """
        return PydanticJSONFileColorPalette(type="JSON FILE", path=PALETTE_FILE_PATH).color_palette


class ColorPaletteCreator(BaseModel):
    """
    A generator for a :class:`~foundry.core.palette.ColorPalette.ColorPaletteProtocol`.
    Creates the color palette dynamically from its type attribute to provide it additional information.
    """

    def __init_subclass__(cls, **kwargs) -> None:
        return super().__init_subclass__(**kwargs)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def as_default(cls) -> PydanticColorPaletteProtocol:
        return PydanticDefaultColorPalette(type="DEFAULT")

    @classmethod
    def generate_color_palette(cls, v: dict) -> PydanticColorPaletteProtocol:
        """
        The constructor for each specific color palette.

        Parameters
        ----------
        v : dict
            The dictionary to create the color palette from.

        Returns
        -------
        PydanticColorPaletteProtocol
            The created layout as defined by `v["type"]`

        Raises
        ------
        NotImplementedError
            If the constructor does not have a valid constructor for `v["type"]`.
        """

        type_ = ColorPaletteType(v["type"])
        if type_ == ColorPaletteType.default:
            return PydanticDefaultColorPalette(**v)
        if type_ == ColorPaletteType.colors:
            return PydanticColorsColorPalette(**v)
        if type_ == ColorPaletteType.palette_file:
            return PydanticPaletteFileColorPalette(**v)
        if type_ == ColorPaletteType.json_file:
            return PydanticJSONFileColorPalette(**v)
        raise NotImplementedError(f"There is no color palette of type {type_}")

    @classmethod
    def validate(cls, v) -> PydanticColorPaletteProtocol:
        """
        Validates that the provided object is a valid color palette.

        Parameters
        ----------
        v : dict
            The dictionary to create the color palette from.

        Returns
        -------
        PydanticColorPaletteProtocol
            If validated, a color palette will be created in accordance to `generate_color_palette`.

        Raises
        ------
        TypeError
            If a dictionary is not provided.
        TypeError
            If the dictionary does not contain the key `"type"`.
        TypeError
            If the type provided is not inside :class:`~foundry.core.palette.ColorPalette.ColorPaletteType`.
        """
        if not isinstance(v, dict):
            raise TypeError("Dictionary required")
        if "type" not in v:
            raise TypeError("Must have a type")
        if not ColorPaletteType.has_value(type_ := v["type"]):
            raise TypeError(f"{type_} is not a valid layout type")
        return cls.generate_color_palette(v)
