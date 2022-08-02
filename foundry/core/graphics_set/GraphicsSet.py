from itertools import chain
from typing import Protocol

from attr import attrs
from pydantic import BaseModel

from foundry.core.graphics_page.GraphicsPage import (
    GraphicsPageProtocol,
    PydanticGraphicsPage,
)
from foundry.core.graphics_set.util import get_graphics_pages_from_tileset


class GraphicsSetProtocol(Protocol):
    """
    A representation of a series of graphical pages inside the ROM.

    Attributes
    ----------
    pages: tuple[GraphicsPageProtocol, ...]
        The pages that compose the graphical set.
    """

    pages: tuple[GraphicsPageProtocol, ...]

    def __bytes__(self) -> bytes:
        ...


@attrs(slots=True, auto_attribs=True, frozen=True, eq=False, hash=False)
class GraphicsSet:
    """
    A representation of a series of graphical pages inside the ROM, that uses ``attrs`` to create
    a basic implementation.

    Attributes
    ----------
    pages: tuple[GraphicsPageProtocol, ...]
        The pages that compose the graphical set.
    """

    pages: tuple[GraphicsPageProtocol, ...]

    def __eq__(self, other):
        return self is other or (isinstance(other, GraphicsSet) and self.pages == other.pages)

    def __hash__(self) -> int:
        # Just copy the first page's hash
        return hash(self.pages[0]) if self.pages else 0

    def __bytes__(self) -> bytes:
        return bytes(chain.from_iterable([bytes(page) for page in self.pages]))

    @classmethod
    def from_tileset(cls, index: int):
        cls.number = index
        return cls(get_graphics_pages_from_tileset(index))


class PydanticGraphicsSet(BaseModel):
    """
    A JSON model of a generic GraphicsSet through Pydantic.

    Attributes
    ----------
    pages: list[PydanticGraphicsPage]
        The pages that compose the graphical set.
    """

    pages: list[PydanticGraphicsPage]

    @property
    def graphics_set(self) -> GraphicsSetProtocol:
        return GraphicsSet(tuple(page.to_graphics_page() for page in self.pages))
