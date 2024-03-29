import abc

from foundry.core.geometry import Point
from foundry.smb3parse.levels import LevelBase


class LevelLike(LevelBase, abc.ABC):
    width: int
    height: int

    def __init__(self, tileset, layout_address):
        super().__init__(tileset, layout_address)

        self.changed = False

    @abc.abstractmethod
    def index_of(self, obj):
        pass

    @abc.abstractmethod
    def object_at(self, point: Point):
        pass

    @abc.abstractmethod
    def get_object_names(self):
        pass

    @abc.abstractmethod
    def get_all_objects(self):
        pass

    @abc.abstractmethod
    def get_object(self, index):
        pass

    @abc.abstractmethod
    def remove_object(self, obj):
        pass

    @abc.abstractmethod
    def draw(self, dc, block_length, transparency, show_expansion):
        pass

    @abc.abstractmethod
    def to_bytes(self):
        pass

    @abc.abstractmethod
    def from_bytes(self, object_data, enemy_data):
        pass
