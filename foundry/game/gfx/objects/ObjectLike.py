from abc import ABC, abstractmethod

from PySide6.QtCore import QRect

from foundry.core.Position import PositionProtocol

EXPANDS_NOT = 0b00
EXPANDS_HORIZ = 0b01
EXPANDS_VERT = 0b10
EXPANDS_BOTH = EXPANDS_HORIZ | EXPANDS_VERT


class ObjectLike(ABC):
    obj_index: int
    name: str

    rect: QRect

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
    def move_by(self, dx, dy):
        pass

    @property
    @abstractmethod
    def position(self) -> PositionProtocol:
        pass

    @position.setter
    @abstractmethod
    def position(self, position: PositionProtocol) -> None:
        pass

    @abstractmethod
    def resize_by(self, dx, dy):
        pass

    @abstractmethod
    def point_in(self, x, y):
        pass

    def get_rect(self, block_length=1) -> QRect:
        if block_length != 1:
            x, y = self.rect.topLeft().toTuple()
            w, h = self.rect.size().toTuple()

            x *= block_length
            w *= block_length
            y *= block_length
            h *= block_length

            return QRect(x, y, w, h)
        else:
            return self.rect

    @abstractmethod
    def change_type(self, new_type):
        pass

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
