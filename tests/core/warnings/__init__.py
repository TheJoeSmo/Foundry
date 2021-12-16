from attr import attrs

from foundry.core.Position import Position


@attrs(slots=True, frozen=True, auto_attribs=True)
class ObjectLike:
    x: int = 0
    y: int = 0
    name: str = ""
    rendered_height: int = 0

    def get_rect(self):
        return True

    @property
    def position(self) -> Position:
        return Position(self.x, self.y)
