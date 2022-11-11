from attr import attrs

from foundry.core.geometry import Point, Rect, Size


@attrs(slots=True, frozen=True, auto_attribs=True)
class ObjectLike:
    x: int = 0
    y: int = 0
    name: str = ""
    rendered_width: int = 0
    rendered_height: int = 0

    def get_rect(self):
        return self.rect

    @property
    def rect(self) -> Rect:
        return Rect(self.point, self.rendered_size)

    @property
    def point(self) -> Point:
        return Point(self.x, self.y)

    @property
    def rendered_size(self) -> Size:
        return Size(self.rendered_width, self.rendered_height)
