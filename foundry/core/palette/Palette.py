from collections.abc import Sequence

from attr import attrs, evolve
from PySide6.QtGui import QColor

from foundry.core.namespace import (
    ConcreteValidator,
    IntegerValidator,
    KeywordValidator,
    SequenceValidator,
    custom_validator,
    validate,
)
from foundry.core.palette import COLORS_PER_PALETTE
from foundry.core.palette.ColorPalette import ColorPalette
from foundry.game.File import ROM


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

    def __getitem__(self, item: int) -> int:
        return self.color_indexes[item]

    @property
    def colors(self) -> Sequence[QColor]:
        return [
            self.color_palette.colors[index % len(self.color_palette.colors)].qcolor for index in self.color_indexes
        ]

    @classmethod
    def as_empty(cls):
        """
        Makes an empty palette of default values.

        Returns
        -------
        AbstractPalette
            A palette filled with default values.
        """
        return cls((0, 0, 0, 0))

    @classmethod
    def from_rom(cls, address: int):
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
        return cls(tuple(int(i) for i in ROM().read(address, COLORS_PER_PALETTE)))

    @classmethod
    @validate(color_indexes=SequenceValidator.generate_class(IntegerValidator), color_palette=ColorPalette)
    def validate_from_colors(cls, color_indexes: Sequence[int], color_palette: ColorPalette):
        return cls(tuple(color_indexes), color_palette)

    @classmethod
    @validate(address=IntegerValidator)
    def validate_from_rom_address(cls, address: int):
        return cls.from_rom(address)

    def evolve_color_index(self, index: int, color_index: int):
        color_indexes = list(self.color_indexes)
        color_indexes[index] = color_index
        return evolve(self, color_indexes=tuple(color_indexes))
