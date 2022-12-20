from __future__ import annotations

from collections.abc import Generator, Iterable, Iterator, Sequence
from colorsys import hsv_to_rgb, rgb_to_hsv
from functools import cache
from json import loads
from pathlib import Path
from typing import ClassVar, Self, overload

from attr import attrs, evolve, field, validators
from PySide6.QtGui import QColor

from foundry import data_dir
from foundry.core import sequence_to_pretty_str
from foundry.core.file import FilePath
from foundry.core.namespace import (
    ConcreteValidator,
    IntegerValidator,
    KeywordValidator,
    SequenceValidator,
    custom_validator,
    default_validator,
    validate,
)
from foundry.game.File import ROM
from foundry.smb3parse.constants import BASE_OFFSET, Palette_By_Tileset, PalSet_Maps

MAP_PALETTE_ADDRESS = PalSet_Maps
PRG_SIZE = 0x2000
PALETTE_PRG_NO = 22
PALETTE_BASE_ADDRESS = BASE_OFFSET + PALETTE_PRG_NO * PRG_SIZE
PALETTE_OFFSET_LIST = Palette_By_Tileset
PALETTE_OFFSET_SIZE = 2  # bytes
PALETTE_GROUPS_PER_OBJECT_SET = 8
ENEMY_PALETTE_GROUPS_PER_OBJECT_SET = 4
PALETTES_PER_PALETTES_GROUP = 4
COLORS_PER_PALETTE = 4
COLOR_SIZE = 1  # byte
PALETTE_DATA_SIZE = (
    (PALETTE_GROUPS_PER_OBJECT_SET + ENEMY_PALETTE_GROUPS_PER_OBJECT_SET)
    * PALETTES_PER_PALETTES_GROUP
    * COLORS_PER_PALETTE
)
COLOR_COUNT = 64
BYTES_IN_COLOR = 3 + 1  # bytes + separator
PALETTE_FILE_PATH = data_dir / "palette.json"
PALETTE_FILE_COLOR_OFFSET = 0x18


def _check_in_color_range(inst, attr, value):
    if not 0 <= value <= 0xFF:
        raise ValueError(f"{value} is not inside the range 0-255")
    return value


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
    return PALETTE_BASE_ADDRESS + ROM.as_default().endian(PALETTE_OFFSET_LIST + (tileset * PALETTE_OFFSET_SIZE))


@attrs(slots=True, frozen=True, eq=True, hash=True)
@default_validator
class Color(ConcreteValidator, KeywordValidator):
    """
    A representation of a the spectral light perceived.  The commonplace representation is RGBA, (red, green, blue,
    and alpha).  There are also alternative representations supported, such as HSV (hue, saturation, and value).

    Attributes
    ----------
    red: int
        An integer between 0 and 255 that represents the proportion of red to use.
    green: int
        An integer between 0 and 255 that represents the proportion of green to use.
    blue: int
        An integer between 0 and 255 that represents the proportion of blue to use.
    alpha: int
        An integer between 0 and 255 that represents how transparent the color is.
    hue: int
        An integer between 0 and 359 that represents the hue of the color.
    saturation: int
        An integer between 0 and 255 that represents the saturation of the color.
    value: int
        An integer between 0 and 255 that represents the value of the color.
    r: float
        A float between 0.0 and 1.0 that represents the proportion of red to use.
    g: float
        A float between 0.0 and 1.0 that represents the proportion of green to use.
    b: float
        A float between 0.0 and 1.0 that represents the proportion of blue to use.
    a: float
        A float between 0.0 and 1.0 that represents how transparent the color is.
    h: float
        A float between 0.0 and 1.0 that represents the hue of the color.
    s: float
        A float between 0.0 and 1.0 that represents the saturation of the color.
    v: float
        A float between 0.0 and 1.0 that represents the value of the color.
    """

    __names__ = ("__COLOR_VALIDATOR__", "color", "Color", "COLOR")
    __required_validators__ = (IntegerValidator,)

    red: int = field(validator=[validators.instance_of(int), _check_in_color_range])
    green: int = field(validator=[validators.instance_of(int), _check_in_color_range])
    blue: int = field(validator=[validators.instance_of(int), _check_in_color_range])
    alpha: int = field(default=0xFF, validator=[validators.instance_of(int), _check_in_color_range])

    def __str__(self) -> str:
        if self.alpha == 0xFF:
            return f"<{self.red:02X}{self.green:02X}{self.blue:02X}>"
        else:
            return f"<{self.red:02X}{self.green:02X}{self.blue:02X}{self.alpha:02X}>"

    def __len__(self) -> int:
        return 4

    def __iter__(self) -> Iterator[int]:
        def iterator() -> Generator[int, None, None]:
            yield self.red
            yield self.green
            yield self.blue
            yield self.alpha

        return iterator()

    def __getitem__(self, index: int) -> int:
        match index:
            case 0:
                return self.red
            case 1:
                return self.green
            case 2:
                return self.blue
            case 3:
                return self.alpha
            case _:
                return NotImplemented

    @property
    def r(self) -> float:
        """
        The proportion of red inside the color.

        Returns
        -------
        float
            A float between 0.0 and 1.0 that represents the proportion of red to use.
        """
        return self.red / 255

    @property
    def g(self) -> float:
        """
        The proportion of green inside the color.

        Returns
        -------
        float
            A float between 0.0 and 1.0 that represents the proportion of green to use.
        """
        return self.green / 255

    @property
    def b(self) -> float:
        """
        The proportion of blue inside the color.

        Returns
        -------
        float
            A float between 0.0 and 1.0 that represents the proportion of blue to use.
        """
        return self.blue / 255

    @property
    def a(self) -> float:
        """
        The proportion of how transparent the color is.

        Returns
        -------
        float
            A float between 0.0 and 1.0 that represents how transparent the color is.
        """
        return self.alpha / 255

    @property
    def hue(self) -> int:
        """
        The hue of the color.

        Returns
        -------
        int
            An integer between 0 and 359 that represents the hue of the color.
        """
        return int(self.h * 359)

    @property
    def h(self) -> float:
        """
        The hue of the color.

        Returns
        -------
        float
            A float between 0.0 and 1.0 that represents the hue of the color.
        """
        return rgb_to_hsv(self.r, self.g, self.b)[0]

    @property
    def saturation(self) -> int:
        """
        The saturation of the color.

        Returns
        -------
        int
            An integer between 0 and 255 that represents the saturation of the color.
        """
        return int(self.s * 255)

    @property
    def s(self) -> float:
        """
        The saturation of the color.

        Returns
        -------
        float
            A float between 0.0 and 1.0 that represents the saturation of the color.
        """
        return rgb_to_hsv(self.r, self.g, self.b)[1]

    @property
    def value(self) -> int:
        """
        The value of the color.

        Returns
        -------
        int
            An integer between 0 and 255 that represents the value of the color.
        """
        return int(self.v * 255)

    @property
    def v(self) -> float:
        """
        The value of the color.

        Returns
        -------
        float
            A float between 0.0 and 1.0 that represents the value of the color.
        """
        return rgb_to_hsv(self.r, self.g, self.b)[2]

    @classmethod
    @validate(red=IntegerValidator, green=IntegerValidator, blue=IntegerValidator, alpha=IntegerValidator)
    def validate(cls, red: int, green: int, blue: int, alpha: int):
        return cls(red, green, blue, alpha)

    @classmethod
    def ensure_type(cls, color) -> Self:
        match color:
            case Color():
                return color
            case QColor():
                return cls.from_qt(color)
            case _:
                return NotImplemented

    @classmethod
    def from_hsv(cls, hue: float, saturation: float, value: float) -> Self:
        """
        Generates a color from a hue, saturation, and value.

        Parameters
        ----------
        hue : float
            The hue of the color.
        saturation : float
            The saturation of the color.
        value : float
            The value of the color.

        Returns
        -------
        Self
            The RGBA representation of the color.
        """
        return cls(*map(lambda v: int(v * 255), hsv_to_rgb(hue, saturation, value)))

    @classmethod
    def from_qt(cls, color: QColor) -> Self:
        return cls(color.red(), color.green(), color.blue(), color.alpha())

    def to_qt(self) -> QColor:
        return QColor(self.red, self.green, self.blue, self.alpha)

    def to_rgb_bytes(self) -> bytes:
        return self.red.to_bytes(1, "little") + self.green.to_bytes(1, "little") + self.blue.to_bytes(1, "little")


class ColorSequence(Sequence):
    __slots__ = ("_list",)
    _list: list[Color]

    def __init__(self, iterable: Iterable[Color | QColor]):
        self._list = [Color.ensure_type(c) for c in iterable]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._list})"

    def __str__(self) -> str:
        return f"<{sequence_to_pretty_str(self._list)}>"

    def __len__(self) -> int:
        return len(self._list)

    @overload
    def __getitem__(self, index: int) -> Color:
        pass

    @overload
    def __getitem__(self, index: Color | QColor) -> int:
        pass

    def __getitem__(self, index: int | Color | QColor) -> int | Color:
        match index:
            case int():
                return self._list[index % len(self._list)]
            case Color():
                return self._list.index(index)
            case QColor():
                return self._list.index(Color.from_qt(index))
            case _:
                return NotImplemented

    def __iter__(self) -> Iterator[Color]:
        return iter(self._list)

    def __contains__(self, value: int | Color | QColor) -> bool:
        match value:
            case int():
                return 0 <= value <= len(self._list)
            case Color():
                return value in self._list
            case QColor():
                return Color.from_qt(value) in self._list
            case _:
                return NotImplemented

    def __reversed__(self) -> Iterator[Color]:
        return reversed(self._list)

    def index(self, value: Color | QColor, start: int = 0, stop: int | None = None) -> int:
        match value:
            case Color():
                return self._list.index(value, start, stop)  # type: ignore
            case QColor():
                return self._list.index(Color.from_qt(value), start, stop)  # type: ignore
            case _:
                return NotImplemented

    def count(self, value: Color | QColor) -> int:
        match value:
            case Color():
                return self._list.count(value)
            case QColor():
                return self._list.count(Color.from_qt(value))
            case _:
                return NotImplemented


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
    _default: ClassVar[ColorPalette | None] = None

    colors: ColorSequence

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.colors})"

    @overload
    def __getitem__(self, item: int) -> Color:
        pass

    @overload
    def __getitem__(self, item: Color) -> int:
        pass

    @overload
    def __getitem__(self, item: QColor) -> int:
        pass

    def __getitem__(self, item: int | Color | QColor) -> int | Color:
        return self.colors[item]

    @classmethod
    @validate(colors=SequenceValidator.generate_class(Color))
    def validate_from_colors(cls, colors: Sequence[Color | QColor]) -> Self:
        return cls(ColorSequence(colors))

    @classmethod
    def from_palette_file(cls, path: Path) -> Self:
        with open(path, "rb") as f:
            data = f.read()
        return cls(ColorSequence(Color(*data[i : i + 4]) for i in range(PALETTE_FILE_COLOR_OFFSET, len(data), 4)))

    @classmethod
    @validate(path=FilePath)
    def validate_from_palette_file(cls, path: FilePath) -> Self:
        return cls.from_palette_file(path)

    @classmethod
    def from_json_file(cls, path: Path) -> Self:
        with open(path) as f:
            return cls(ColorSequence(Color(**c) for c in loads(f.read())["colors"]))

    @classmethod
    @validate(path=FilePath)
    def validate_from_json_file(cls, path: FilePath) -> Self:
        return cls.from_json_file(path)

    @classmethod
    def from_default(cls) -> Self:
        if cls._default is None:
            cls._default = cls.from_json_file(PALETTE_FILE_PATH)
        return cls._default

    @classmethod
    @validate()
    def validate_from_default(cls) -> Self:
        return cls.from_default()

    def index(self, value: Color | QColor, start: int = 0, stop: int | None = None) -> int:
        return self.colors.index(value, start, stop)

    def count(self, value: Color | QColor) -> int:
        return self.colors.count(value)


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
@custom_validator("COLORS", method_name="validate_from_colors")
@custom_validator("ROM ADDRESS", method_name="validate_from_rom_address")
class Palette(ConcreteValidator, KeywordValidator):
    __names__ = ("__PALETTE_VALIDATOR__", "palette", "Palette", "PALETTE")
    __required_validators__ = (SequenceValidator, IntegerValidator, ColorPalette)

    color_indexes: tuple[int, ...]
    color_palette: ColorPalette = ColorPalette.from_default()

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.color_indexes})"

    def __bytes__(self) -> bytes:
        return bytes(i & 0xFF for i in self.color_indexes)

    @overload
    def __getitem__(self, item: int) -> int:
        pass

    @overload
    def __getitem__(self, item: tuple[int, type[Color]]) -> Color:
        pass

    @overload
    def __getitem__(self, item: tuple[int, type[QColor]]) -> QColor:
        pass

    @overload
    def __getitem__(self, item: Color | QColor) -> int:
        pass

    # flake8: noqa: E211, F821
    def __getitem__(
        self, item: int | Color | QColor | tuple[int, type[Color]] | tuple[int, type[QColor]]
    ) -> int | Color | QColor:
        match item:
            case int():
                return self.color_indexes[item]
            case Color() | QColor():
                return self.color_palette[item]
            case [i, t] if t == Color:
                return self.color_palette[self.color_indexes[i]]
            case [i, t] if t == QColor:
                return self.color_palette[self.color_indexes[i]].to_qt()
            case _:
                return NotImplemented

    def __iter__(self) -> Iterator[Color]:
        def iterate() -> Generator[Color, None, None]:
            for index in self.color_indexes:
                yield self.color_palette[index]

        return iterate()

    def __contains__(self, value: int | Color | QColor) -> bool:
        match value:
            case int():
                return value in self.color_indexes
            case Color():
                return value in set(self)
            case QColor():
                return Color.from_qt(value) in set(self)
            case _:
                return NotImplemented

    @classmethod
    def as_empty(cls) -> Self:
        """
        Makes an empty palette of default values.

        Returns
        -------
        AbstractPalette
            A palette filled with default values.
        """
        return cls((0, 0, 0, 0))

    @classmethod
    def from_rom(cls, address: int) -> Self:
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
        return cls(tuple(int(i) for i in ROM.as_default()[address : address + COLORS_PER_PALETTE]))

    @classmethod
    @validate(color_indexes=SequenceValidator.generate_class(IntegerValidator), color_palette=ColorPalette)
    def validate_from_colors(cls, color_indexes: Sequence[int], color_palette: ColorPalette) -> Self:
        return cls(tuple(color_indexes), color_palette)

    @classmethod
    @validate(address=IntegerValidator)
    def validate_from_rom_address(cls, address: int) -> Self:
        return cls.from_rom(address)

    def index(self, value: int | Color | QColor) -> int:
        match value:
            case int():
                return self.color_indexes.index(value)
            case Color() | QColor():
                return self.color_palette.index(value)
            case _:
                return NotImplemented

    def evolve_color_index(self, index: int, color_index: int) -> Self:
        color_indexes = list(self.color_indexes)
        color_indexes[index] = color_index
        return evolve(self, color_indexes=tuple(color_indexes))


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
@default_validator
class PaletteGroup(ConcreteValidator, KeywordValidator):
    """
    A concrete implementation of a hashable and immutable group of palettes.
    """

    __names__ = ("__PALETTE_GROUP_VALIDATOR__", "palette group", "Palette Group", "PALETTE GROUP")
    __required_validators__ = (SequenceValidator, Palette)

    palettes: tuple[Palette]

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({[str(p) for p in self.palettes]})"

    def __bytes__(self) -> bytes:
        b = bytearray()
        for palette in self.palettes:
            b.extend(bytes(palette))
        return bytes(b)

    @overload
    def __getitem__(self, item: int) -> Palette:
        pass

    @overload
    def __getitem__(self, item: tuple[int, int]) -> int:
        pass

    @overload
    def __getitem__(self, item: tuple[int, int, type[Color]]) -> Color:
        pass

    @overload
    def __getitem__(self, item: tuple[int, int, type[QColor]]) -> QColor:
        pass

    def __getitem__(
        self, item: int | tuple[int, int] | tuple[int, int, type[Color]] | tuple[int, int, type[QColor]]
    ) -> Palette | int | Color | QColor:
        match item:
            case int():
                return self.palettes[item]
            case [palette_index, color_index]:
                return self.palettes[palette_index][color_index]
            case [palette_index, color_index, t] if t == Color:
                return self.palettes[palette_index][color_index, Color]
            case [palette_index, color_index, t] if t == QColor:
                return self.palettes[palette_index][color_index, QColor]
            case _:
                return NotImplemented

    @property
    def background_color(self) -> QColor:
        return self.palettes[0][0, QColor]

    @classmethod
    def as_empty(cls) -> Self:
        """
        Makes an empty palette group of default values.

        Returns
        -------
        AbstractPaletteGroup
            The palette group filled with default values.
        """
        return cls(tuple(Palette.as_empty() for _ in range(PALETTES_PER_PALETTES_GROUP)))

    @classmethod
    def from_rom(cls, address: int) -> Self:
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
        return cls(
            tuple(
                Palette.from_rom(address + offset)
                for offset in [COLORS_PER_PALETTE * i for i in range(PALETTES_PER_PALETTES_GROUP)]
            )
        )

    @classmethod
    def from_tileset(cls, tileset: int, index: int) -> Self:
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
        PaletteGroup
            The PaletteGroup that represents the tileset's palette group at the provided offset.
        """
        offset = get_internal_palette_offset(tileset) + index * PALETTES_PER_PALETTES_GROUP * COLORS_PER_PALETTE
        return cls.from_rom(offset)

    @classmethod
    @validate(palettes=SequenceValidator.generate_class(Palette))
    def validate(cls, palettes: Sequence[Palette]) -> Self:
        return cls(tuple(palettes))

    def evolve_palettes(self, palette_index: int, palette: Palette) -> Self:
        palettes: Iterable[Palette] = list(self.palettes)
        palettes[palette_index] = palette
        if any(map(lambda p: p != palette, palettes)):
            palettes = map(lambda p: p.evolve_color_index(0, palette[0]), palettes)
        return evolve(self, palettes=tuple(palettes))
