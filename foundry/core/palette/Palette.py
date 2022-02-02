from typing import Protocol

from attr import attrs
from PySide6.QtGui import QColor

from foundry.core.palette import COLORS_PER_PALETTE, NESPalette
from foundry.game.File import ROM


class MutablePaletteProtocol(Protocol):
    color_indexes: list[int]

    def __bytes__(self) -> bytes:
        ...

    def __getitem__(self, item: int) -> int:
        ...

    def __setitem__(self, key: int, value: int):
        ...

    @property
    def colors(self) -> list[QColor]:
        ...


@attrs(slots=True, auto_attribs=True)
class MutablePalette:
    color_indexes: list[int]

    def __bytes__(self) -> bytes:
        return bytes([i & 0xFF for i in self.color_indexes])

    def __getitem__(self, item: int) -> int:
        return self.color_indexes[item]

    def __setitem__(self, key: int, value: int):
        self.color_indexes[key] = value

    @classmethod
    def as_empty(cls):
        """
        Makes an empty palette of default values

        Returns
        -------
        MutablePalette
            A palette filled with default values.
        """
        return cls([0, 0, 0, 0])

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
        MutablePalette
            The palette that represents the absolute address in ROM.
        """
        return cls([int(i) for i in ROM().read(address, COLORS_PER_PALETTE)])

    @property
    def colors(self) -> list[QColor]:
        return [NESPalette[c & 0x3F] for c in self.color_indexes]
