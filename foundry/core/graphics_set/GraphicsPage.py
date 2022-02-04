from typing import Protocol

from attr import attrs

from foundry.game.File import ROM

CHR_ROM_OFFSET = 0x40010
CHR_ROM_SEGMENT_SIZE = 0x400


class GraphicalPageProtocol(Protocol):
    """
    A representation of a single page of graphics inside the ROM.

    Attributes
    ----------
    index: int
        The index of the graphical page into the ROM.
    """

    index: int

    def __bytes__(self) -> bytes:
        ...


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class GraphicalPage:
    """
    A representation of a single page of graphics inside the ROM, that uses ``attrs`` to create a
    basic implementation.

    Attributes
    ----------
    index: int
        The index of the graphical page into the ROM.
    """

    index: int

    @property
    def rom_offset(self) -> int:
        return CHR_ROM_OFFSET + self.index * CHR_ROM_SEGMENT_SIZE

    def __bytes__(self) -> bytes:
        return bytes(ROM().bulk_read(CHR_ROM_SEGMENT_SIZE, self.rom_offset))
