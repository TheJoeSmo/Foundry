from collections.abc import Sequence
from json import loads
from pathlib import Path

from attr import attrs

from foundry.core.file import FilePath
from foundry.core.namespace import (
    ConcreteValidator,
    KeywordValidator,
    SequenceValidator,
    custom_validator,
    validate,
)
from foundry.core.palette import PALETTE_FILE_COLOR_OFFSET, PALETTE_FILE_PATH
from foundry.core.palette.Color import Color


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
@custom_validator("DEFAULT", method_name="validate_from_default")
@custom_validator("COLORS", method_name="validate_from_colors")
@custom_validator("PALETTE FILE", method_name="validate_from_palette_file")
@custom_validator("JSON FILE", method_name="validate_from_json_file")
class ColorPalette(ConcreteValidator, KeywordValidator):
    """
    A representation of a series of colors.
    """

    __names__ = ("__COLOR_PALETTE_VALIDATOR__", "color palette", "Color Palette", "COLOR PALETTE")
    __required_validators__ = (SequenceValidator, Color, FilePath)

    colors: tuple[Color, ...]

    @classmethod
    @validate(colors=SequenceValidator.generate_class(Color))
    def validate_from_colors(cls, colors: Sequence[Color]):
        return cls(tuple(colors))

    @classmethod
    def from_palette_file(cls, path: Path):
        with open(path, "rb") as f:
            data = f.read()
        return cls(tuple(Color(*data[i : i + 4]) for i in range(PALETTE_FILE_COLOR_OFFSET, len(data), 4)))

    @classmethod
    @validate(path=FilePath)
    def validate_from_palette_file(cls, path: FilePath):
        return cls.from_palette_file(path)

    @classmethod
    def from_json_file(cls, path: Path):
        with open(path) as f:
            return cls(tuple(Color(**c) for c in loads(f.read())["colors"]))

    @classmethod
    @validate(path=FilePath)
    def validate_from_json_file(cls, path: FilePath):
        return cls.from_json_file(path)

    @classmethod
    def from_default(cls):
        return cls.from_json_file(PALETTE_FILE_PATH)

    @classmethod
    @validate()
    def validate_from_default(cls):
        return cls.from_default()
