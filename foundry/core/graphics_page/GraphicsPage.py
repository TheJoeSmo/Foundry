from pathlib import Path
from typing import TypeVar

from attr import attrs

from foundry.core.file import FilePath
from foundry.core.graphics_page import CHR_ROM_SEGMENT_SIZE
from foundry.core.namespace import (
    ConcreteValidator,
    IntegerValidator,
    KeywordValidator,
    OptionalValidator,
    default_validator,
    validate,
)
from foundry.game.File import ROM, INESHeader

_P = TypeVar("_P", bound="GraphicsPage")


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=False)
@default_validator
class GraphicsPage(ConcreteValidator, KeywordValidator):
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
    path: Path | None = None
    __names__ = ("__GRAPHICS_PAGE_VALIDATOR__", "graphics page", "page", "Page", "PAGE")
    __required_validators__ = (IntegerValidator, FilePath, OptionalValidator)

    @property
    def offset(self) -> int:
        return ROM.as_default().header.program_size + self.index * CHR_ROM_SEGMENT_SIZE + INESHeader.INES_HEADER_SIZE

    def __hash__(self) -> int:
        # We will assume that the path is the same most of the time to make hashing faster.
        return self.index

    def __bytes__(self) -> bytes:
        if self.path is None:
            return bytes(ROM.as_default()[slice(self.offset, self.offset + CHR_ROM_SEGMENT_SIZE), True])
        with open(self.path, "rb") as f:
            return f.read()[CHR_ROM_SEGMENT_SIZE * self.offset : CHR_ROM_SEGMENT_SIZE * (self.offset + 1)]

    @classmethod
    @validate(index=IntegerValidator, path=OptionalValidator.generate_class(FilePath))
    def validate(cls: type[_P], index: int, path: Path | None) -> _P:
        return cls(index, path)
