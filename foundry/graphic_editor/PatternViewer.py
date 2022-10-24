from attr import attrs
from PySide6.QtCore import QPoint, QRect, Signal, SignalInstance
from PySide6.QtGui import QBrush, QColor, QMouseEvent, QPainter, QPaintEvent, Qt
from PySide6.QtWidgets import QLayout, QWidget

from foundry.core.geometry import Point
from foundry.core.graphics_page.GraphicsGroup import GraphicsGroupProtocol
from foundry.core.graphics_set.GraphicsSet import GraphicsSet
from foundry.core.palette import PaletteGroup
from foundry.core.tiles import MASK_COLOR
from foundry.game.gfx.drawable.Tile import Tile


@attrs(slots=True, auto_attribs=True)
class PatternViewerModel:
    groups: list[GraphicsGroupProtocol]
    group_indexes: list[int]
    palette_group: PaletteGroup
    palette_index: int
    zoom: int


class PatternViewerController(QWidget):
    PATTERNS = 256
    PATTERNS_PER_ROW = 16
    PATTERNS_PER_COLUMN = 16

    patterns_changed: SignalInstance = Signal()  # type: ignore
    pattern_selected: SignalInstance = Signal(int)  # type: ignore
    status_message_changed: SignalInstance = Signal(tuple[Point, int])  # type: ignore

    def __init__(
        self,
        parent: QWidget | None,
        groups: list[GraphicsGroupProtocol],
        group_indexes: list[int],
        palette_group: PaletteGroup,
        palette_index: int,
        zoom: int = 4,
    ):
        super().__init__(parent)

        self.model = PatternViewerModel(groups, group_indexes, palette_group, palette_index, zoom)
        self.layout().setSizeConstraint(QLayout.SetFixedSize)

    @property
    def graphics_set(self) -> GraphicsSet:
        return GraphicsSet.from_groups(tuple(self.model.groups), tuple(self.model.group_indexes))

    @property
    def palette_group(self) -> PaletteGroup:
        return self.model.palette_group

    @palette_group.setter
    def palette_group(self, value: PaletteGroup):
        self.model.palette_group = value
        self.update()

    @property
    def palette_index(self) -> int:
        return self.model.palette_index

    @palette_index.setter
    def palette_index(self, value: int):
        self.model.palette_index = value
        self.update()

    @property
    def zoom(self) -> int:
        return self.model.zoom

    @zoom.setter
    def zoom(self, zoom: int):
        self.model.zoom = zoom
        self.update()

    @property
    def pattern_scale(self) -> int:
        return Tile.WIDTH * self.zoom  # type: ignore

    def normalize_point(self, point: Point | QPoint) -> Point:
        if isinstance(point, QPoint):
            point = Point.from_qpoint(point)
        return point // Point(self.pattern_scale, self.pattern_scale)

    def index(self, point: Point) -> int:
        return point.y * self.PATTERNS_PER_ROW + point.x

    def mouseMoveEvent(self, event: QMouseEvent):
        self.status_message_changed.emit(((point := self.normalize_point(event.pos())), self.index(point)))

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.pattern_selected.emit(self.index(self.normalize_point(event.pos())))

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)

        painter.setBrush(QBrush(self.palette_group.background_color))
        painter.drawRect(QRect(QPoint(0, 0), self.size()))

        for i in range(self.PATTERNS):
            tile = Tile(i, self.palette_group, self.palette_index, self.graphics_set)

            x = (i % self.PATTERNS_PER_ROW) * self.pattern_scale
            y = (i // self.PATTERNS_PER_ROW) * self.pattern_scale

            image = tile.as_image(self.pattern_scale)
            mask = image.createMaskFromColor(QColor(*MASK_COLOR).rgb(), Qt.MaskOutColor)
            image.setAlphaChannel(mask)
            painter.drawImage(x, y, image)
