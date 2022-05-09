from attr import attrs

from foundry.core.point.Point import MutablePoint
from foundry.core.size.Size import MutableSize


@attrs(slots=True, frozen=True, auto_attribs=True)
class ObjectLike:
    x: int = 0
    y: int = 0
    name: str = ""
    rendered_width: int = 0
    rendered_height: int = 0

    def get_rect(self):
        return True

    @property
    def position(self) -> MutablePoint:
        return MutablePoint(self.x, self.y)

    @property
    def rendered_size(self) -> MutableSize:
        return MutableSize(self.rendered_width, self.rendered_height)
