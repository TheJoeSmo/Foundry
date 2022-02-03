from itertools import chain
from typing import Protocol

from attr import attrs

from foundry.core.graphics_set.GraphicsPage import GraphicalPageProtocol
from foundry.core.graphics_set.util import get_graphics_pages_from_tileset


class GraphicsSetProtocol(Protocol):
    """
    A representation of a series of graphical pages inside the ROM.

    Attributes
    ----------
    pages: tuple[GraphicalPageProtocol, ...]
        The pages that compose the graphical set.
    """

    pages: tuple[GraphicalPageProtocol, ...]

    def __bytes__(self) -> bytes:
        ...


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class GraphicsSet:
    """
    A representation of a series of graphical pages inside the ROM, that uses ``attrs`` to create
    a basic implementation.

    Attributes
    ----------
    pages: tuple[GraphicalPageProtocol, ...]
        The pages that compose the graphical set.
    """

    pages: tuple[GraphicalPageProtocol, ...]

    def __bytes__(self) -> bytes:
        return bytes(chain.from_iterable([bytes(page) for page in self.pages]))

    @classmethod
    def from_tileset(cls, index: int):
        cls.number = index
        return cls(get_graphics_pages_from_tileset(index))
