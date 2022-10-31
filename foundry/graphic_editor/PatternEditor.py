from enum import Enum

from attr import attrs
from PySide6.QtCore import QPoint, QRect, QSize, Signal, SignalInstance
from PySide6.QtGui import QBrush, QColor, QMouseEvent, QPainter, QPaintEvent, Qt
from PySide6.QtWidgets import QLayout, QWidget

from foundry.core.geometry import Point, Size
from foundry.core.graphics_page.GraphicsGroup import GraphicsGroup
from foundry.core.graphics_set.GraphicsSet import GraphicsSet
from foundry.core.gui import controller
from foundry.core.palette import PaletteGroup
from foundry.core.tiles import MASK_COLOR
from foundry.game.gfx.drawable.Tile import Tile
from foundry.graphic_editor.PatternMatrix import PatternMatrix


class PatternEditorMode(int, Enum):
    SELECT_PATTERNS = 0
    DRAW = 1


@attrs(slots=True, auto_attribs=True)
class PatternEditorModel:
    groups: list[GraphicsGroup]
    group_indexes: list[int]
    palette_group: PaletteGroup
    palette_index: int
    matrix: PatternMatrix
    max_size: Size
    zoom: int


@controller(PatternEditorModel)
class PatternEditorController(QWidget, PatternEditorModel):
    patterns_changed: SignalInstance = Signal()  # type: ignore
    pattern_selected: SignalInstance = Signal(int)  # type: ignore
    status_message_changed: SignalInstance = Signal(tuple[Point, int])  # type: ignore

    def __init__(
        self,
        parent: QWidget | None,
        groups: list[GraphicsGroup],
        group_indexes: list[int],
        palette_group: PaletteGroup,
        palette_index: int,
        max_size: Size = Size(16, 16),
        zoom: int = 4,
    ):
        super().__init__(parent)

        self.model = PatternEditorModel(
            groups, group_indexes, palette_group, palette_index, PatternMatrix(max_size), max_size, zoom
        )
        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    @property
    def graphics_set(self) -> GraphicsSet:
        return GraphicsSet.from_groups(self.model.groups, self.model.group_indexes)

    @property
    def pattern_scale(self) -> int:
        return Tile.WIDTH * self.zoom  # type: ignore

    @property
    def pattern_size(self) -> Size:
        return Size(self.pattern_scale, self.pattern_scale)

    @property
    def matrix_size(self) -> Size:
        return Size(self.size().width() // self.pattern_scale, self.size().height() // self.pattern_scale)

    def update(self):
        self.model.matrix.size = self.matrix_size

        super().update()

    def sizeHint(self) -> QSize:
        return self.maximumSize()

    def minimumSize(self) -> QSize:
        return self.pattern_size.qsize

    def maximumSize(self) -> QSize:
        return (self.pattern_size * self.model.max_size).qsize

    def normalize_point(self, point: Point | QPoint) -> Point:
        if isinstance(point, QPoint):
            point = Point.from_qt(point)
        return point // Point(self.pattern_scale, self.pattern_scale)

    def index(self, point: Point) -> int:
        return point.y * self.matrix_size.width + point.x

    def mouseMoveEvent(self, event: QMouseEvent):
        self.status_message_changed.emit(((point := self.normalize_point(event.pos())), self.index(point)))

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.pattern_selected.emit(self.index(self.normalize_point(event.pos())))

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)

        painter.setBrush(QBrush(self.palette_group.background_color))
        painter.drawRect(QRect(QPoint(0, 0), self.size()))

        size = self.matrix_size
        for i in range(size.height):
            tile = Tile(i, self.palette_group, self.palette_index, self.graphics_set)

            x = (i % size.width) * self.pattern_scale
            y = (i // size.width) * self.pattern_scale

            image = tile.as_image(self.pattern_scale)
            mask = image.createMaskFromColor(QColor(*MASK_COLOR).rgb(), Qt.MaskMode.MaskMode.MaskOutColor)
            image.setAlphaChannel(mask)
            painter.drawImage(x, y, image)
