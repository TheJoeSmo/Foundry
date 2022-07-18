from collections.abc import Sequence

from attr import attrs

from foundry.core.graphics_page.GraphicsPage import GraphicsPage
from foundry.core.namespace import (
    ConcreteValidator,
    IntegerValidator,
    KeywordValidator,
    SequenceValidator,
    default_validator,
    validate,
)


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
@default_validator
class GraphicsGroup(ConcreteValidator, KeywordValidator):
    """
    A representation of a series of graphical pages that could be animated.

    Attributes
    ----------
    pages: tuple[GraphicsPage, ...]
        The pages to be animated.
    animation_speed: int
        The animation speed in milliseconds.
    """

    pages: tuple[GraphicsPage, ...]
    animation_speed: int

    def get_current_graphics_page(self, time: int) -> GraphicsPage:
        return self.pages[time // self.animation_speed % len(self.pages)]

    @property
    def offsets(self) -> tuple[int]:
        return tuple(o.offset for o in self.pages)

    @classmethod
    @validate(pages=SequenceValidator.generate_class(GraphicsPage), animation_speed=IntegerValidator)
    def validate(cls, pages: Sequence[GraphicsPage], animation_speed: int):
        return cls(tuple(pages), animation_speed)
