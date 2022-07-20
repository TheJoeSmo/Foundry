from collections.abc import Sequence
from itertools import chain
from typing import TypeVar

from attr import attrs

from foundry.core.graphics_page.GraphicsPage import GraphicsPage
from foundry.core.graphics_set.util import get_graphics_pages_from_tileset
from foundry.core.namespace import (
    ConcreteValidator,
    KeywordValidator,
    SequenceValidator,
    default_validator,
    validate,
)

_S = TypeVar("_S", bound="GraphicsSet")


@attrs(slots=True, auto_attribs=True, frozen=True, eq=False, hash=False)
@default_validator
class GraphicsSet(ConcreteValidator, KeywordValidator):
    """
    A representation of a series of graphical pages inside the ROM, that uses ``attrs`` to create
    a basic implementation.

    Attributes
    ----------
    pages: tuple[GraphicsPage, ...]
        The pages that compose the graphical set.
    """

    pages: tuple[GraphicsPage, ...]
    __names__ = (
        "__GRAPHICS_SET_VALIDATOR__",
        "graphics set",
        "Graphics Set",
        "GRAPHICS SET",
    )
    __required_validators__ = (GraphicsPage, SequenceValidator)

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

    @classmethod
    @validate(pages=SequenceValidator.generate_class(GraphicsPage))
    def validate(cls: type[_S], pages: Sequence[GraphicsPage]) -> _S:
        return cls(tuple(pages))
