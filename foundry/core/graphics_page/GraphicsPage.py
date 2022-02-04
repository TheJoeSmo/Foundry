from pathlib import Path
from typing import Optional, Protocol

from attr import attrs
from pydantic import BaseModel, FilePath

from foundry.core.graphics_page import CHR_ROM_OFFSET, CHR_ROM_SEGMENT_SIZE
from foundry.game.File import ROM


class GraphicsPageProtocol(Protocol):
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
class GraphicsPage:
    """
    A representation of a single page of graphics inside the ROM, that uses ``attrs`` to create a
    basic implementation.

    Attributes
    ----------
    index: int
        The index of the graphical page into the ROM.
    path: Optional[Path]
        The path to the file containing the bytes of the graphics page or ROM if None.
    """

    index: int
    path: Optional[Path] = None

    @property
    def offset(self) -> int:
        return CHR_ROM_OFFSET + self.index * CHR_ROM_SEGMENT_SIZE

    def __bytes__(self) -> bytes:
        if self.path is None:
            return bytes(ROM().bulk_read(CHR_ROM_SEGMENT_SIZE, self.offset))
        with open(self.path, "rb") as f:
            return f.read()[CHR_ROM_SEGMENT_SIZE * self.offset : CHR_ROM_SEGMENT_SIZE * (self.offset + 1)]


class PydanticGraphicsPage(BaseModel):
    """
    A JSON model of a generic GraphicsPage through Pydantic

    Attributes
    ----------
    index: int
        The index of the graphical page into the ROM.
    path: Optional[FilePath]
        The path to the file containing the bytes of the graphics page or ROM if None.
    """

    index: int
    path: Optional[FilePath]

    def to_graphics_page(self) -> GraphicsPageProtocol:
        return GraphicsPage(self.index, self.path)
