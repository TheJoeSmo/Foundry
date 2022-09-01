from collections.abc import Iterable, Sequence

from attr import attrs, evolve
from PySide6.QtGui import QColor

from foundry.core.namespace import (
    ConcreteValidator,
    KeywordValidator,
    SequenceValidator,
    default_validator,
    validate,
)
from foundry.core.palette import COLORS_PER_PALETTE, PALETTES_PER_PALETTES_GROUP
from foundry.core.palette.Palette import Palette
from foundry.core.palette.util import get_internal_palette_offset


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

    def __getitem__(self, item: int) -> Palette:
        return self.palettes[item]

    @property
    def background_color(self) -> QColor:
        return self.palettes[0].colors[0]

    @classmethod
    def as_empty(cls):
        """
        Makes an empty palette group of default values.

        Returns
        -------
        AbstractPaletteGroup
            The palette group filled with default values.
        """
        return cls(tuple(Palette.as_empty() for _ in range(PALETTES_PER_PALETTES_GROUP)))

    @classmethod
    def from_rom(cls, address: int):
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
        PaletteGroup
            The PaletteGroup that represents the tileset's palette group at the provided offset.
        """
        offset = get_internal_palette_offset(tileset) + index * PALETTES_PER_PALETTES_GROUP * COLORS_PER_PALETTE
        return cls.from_rom(offset)

    @classmethod
    @validate(palettes=SequenceValidator.generate_class(Palette))
    def validate(cls, palettes: Sequence[Palette]):
        return cls(tuple(palettes))

    def evolve_palettes(self, palette_index: int, palette: Palette):
        palettes: Iterable[Palette] = list(self.palettes)
        palettes[palette_index] = palette
        if any(map(lambda p: p != palette, palettes)):
            palettes = map(lambda p: p.evolve_color_index(0, palette[0]), palettes)
        return evolve(self, palettes=tuple(palettes))
