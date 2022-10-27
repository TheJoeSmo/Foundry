from typing import Any

from attr import attrs

from foundry.core.geometry import Point


@attrs(slots=True, auto_attribs=True, eq=False)
class WorldMapPosition:
    world: Any
    screen: int
    point: Point

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.world}, {self.screen}, {self.point})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, WorldMapPosition):
            return False
        return self.screen == other.screen and self.point == other.point

    @property
    def level_info(self) -> tuple[int, Point]:
        return self.world.level_for_position(self.screen, self.point)

    def can_have_level(self):
        return self.world.is_enterable(self.tile())

    def tile(self):
        return self.world.tile_at(self.screen, self.point)

    def tuple(self):
        return self.world.number, self.screen, self.point
