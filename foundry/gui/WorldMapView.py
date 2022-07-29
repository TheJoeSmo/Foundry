from PySide6.QtCore import QSize
from PySide6.QtGui import QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from foundry.game.level.WorldMap import WorldMap


class WorldMapView(QWidget):
    def __init__(self, parent: QWidget | None, world: WorldMap):
        super().__init__(parent)

        self.world = world
        self.zoom = 2

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)

        self.world.draw(painter, self.zoom)

    def sizeHint(self) -> QSize:
        return self.world.q_size * self.zoom
