from typing import Protocol

from attr import attrs

from foundry.core.graphics_page.GraphicsPage import (
    EditableGraphicsPage,
    GraphicsPageProtocol,
)


class GraphicsGroupProtocol(Protocol):
    """
    A representation of a series of graphical pages that could be animated.

    Attributes
    ----------
    pages: tuple[GraphicsPage, ...]
        The pages to be animated.
    animation_speed: int
        The animation speed in milliseconds.
    """

    pages: tuple[GraphicsPageProtocol, ...]
    animation_speed: int

    @property
    def offsets(self) -> tuple[int]:
        ...


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class GraphicsGroup:
    """
    A representation of a series of graphical pages that could be animated.

    Attributes
    ----------
    pages: tuple[GraphicsPage, ...]
        The pages to be animated.
    animation_speed: int
        The animation speed in milliseconds.
    """

    pages: tuple[GraphicsPageProtocol, ...]
    animation_speed: int

    @property
    def offsets(self) -> tuple[int]:
        return tuple(o.offset for o in self.pages)


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class EditableGraphicsGroup:
    """
    A representation of a series of graphical pages that could be animated that focuses
    on being editable through its `pages`.

    Attributes
    ----------
    pages: tuple[EditableGraphicsPage, ...]
        The pages to be animated.
    animation_speed: int
        The animation speed in milliseconds.
    """

    pages: tuple[EditableGraphicsPage, ...]
    animation_speed: int

    @property
    def offsets(self) -> tuple[int]:
        return tuple(o.offset for o in self.pages)
