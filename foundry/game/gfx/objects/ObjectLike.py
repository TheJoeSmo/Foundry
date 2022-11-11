from abc import ABC, abstractmethod

from foundry.core.geometry import Point, Rect, Size
from foundry.game.Definitions import Definition

EXPANDS_NOT = 0b00
EXPANDS_HORIZ = 0b01
EXPANDS_VERT = 0b10
EXPANDS_BOTH = EXPANDS_HORIZ | EXPANDS_VERT


class ObjectLike(ABC):
    obj_index: int
    name: str
    rect: Rect

    @abstractmethod
    def render(self):
        pass

    @abstractmethod
    def draw(self, dc, zoom, transparent):
        pass

    @abstractmethod
    def get_status_info(self):
        pass

    @abstractmethod
    def move_by(self, point: Point) -> None:
        pass

    @property
    @abstractmethod
    def definition(self) -> Definition:
        pass

    @property
    @abstractmethod
    def point(self) -> Point:
        pass

    @point.setter
    @abstractmethod
    def point(self, point: Point) -> None:
        pass

    @abstractmethod
    def point_in(self, x, y):
        pass

    def get_rect(self, block_length: int = 1) -> Rect:
        return self.rect * Size(block_length, block_length)

    @abstractmethod
    def __contains__(self, point):
        pass

    @abstractmethod
    def to_bytes(self):
        pass

    def expands(self):
        return EXPANDS_NOT

    def primary_expansion(self):
        return EXPANDS_NOT
