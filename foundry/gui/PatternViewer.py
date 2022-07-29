from attr import attrs
from PySide6.QtCore import QPoint, QRect, Signal, SignalInstance
from PySide6.QtGui import (
    QBrush,
    QCloseEvent,
    QColor,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QResizeEvent,
    Qt,
)
from PySide6.QtWidgets import QLayout, QStatusBar, QToolBar, QWidget

from foundry import icon
from foundry.core.geometry import Point
from foundry.core.graphics_set.GraphicsSet import GraphicsSet
from foundry.core.palette import NESPalette
from foundry.core.palette.PaletteGroup import MutablePaletteGroup
from foundry.game.gfx.drawable import MASK_COLOR
from foundry.game.gfx.drawable.Tile import Tile
from foundry.gui.CustomChildWindow import CustomChildWindow


@attrs(slots=True, auto_attribs=True)
class PatternViewerModel:
    graphics_set: GraphicsSet
    palette_group: MutablePaletteGroup
    palette_index: int


class PatternViewerController(CustomChildWindow):
    graphics_set_changed: SignalInstance = Signal(GraphicsSet)  # type: ignore
    palette_group_changed: SignalInstance = Signal(MutablePaletteGroup)  # type: ignore
    palette_index_changed: SignalInstance = Signal(int)  # type: ignore
    pattern_selected: SignalInstance = Signal(int)  # type: ignore
    destroyed: SignalInstance = Signal()  # type: ignore

    def __init__(
        self,
        parent: QWidget | None,
        graphics_set: GraphicsSet,
        palette_group: MutablePaletteGroup,
        palette_index: int,
    ):
        super().__init__(parent, "Pattern Viewer")

        self.model = PatternViewerModel(graphics_set, palette_group, palette_index)
        self.view = PatternViewerView(self, graphics_set, palette_group, palette_index)
        self.setCentralWidget(self.view)
        self.toolbar = QToolBar(self)

        self.view.pattern_selected.connect(self.pattern_selected.emit)

        self.zoom_out_action = self.toolbar.addAction(icon("zoom-out.png"), "Zoom Out")
        self.zoom_in_action = self.toolbar.addAction(icon("zoom-in.png"), "Zoom In")

        def change_zoom(offset: int):
            self.view.zoom += offset

        self.zoom_out_action.triggered.connect(lambda *_: change_zoom(-1))  # type: ignore
        self.zoom_in_action.triggered.connect(lambda *_: change_zoom(1))  # type: ignore

        self.addToolBar(self.toolbar)
        self.setStatusBar(QStatusBar(self))

        self.layout().setSizeConstraint(QLayout.SetFixedSize)

    def closeEvent(self, event: QCloseEvent):
        self.toolbar.close()
        self.destroyed.emit()
        super().closeEvent(event)

    @property
    def graphics_set(self) -> GraphicsSet:
        return self.model.graphics_set

    @graphics_set.setter
    def graphics_set(self, value: GraphicsSet):
        self.model.graphics_set = value
        self.view.graphics_set = value
        self.graphics_set_changed.emit(self.graphics_set)
        self.view.update()

    @property
    def palette_group(self) -> MutablePaletteGroup:
        return self.model.palette_group

    @palette_group.setter
    def palette_group(self, value: MutablePaletteGroup):
        self.model.palette_group = value
        self.view.palette_group = value
        self.palette_group_changed.emit(self.palette_group)
        self.view.update()

    @property
    def palette_index(self) -> int:
        return self.model.palette_index

    @palette_index.setter
    def palette_index(self, value: int):
        self.model.palette_index = value
        self.view.palette_index = value
        self.palette_index_changed.emit(self.palette_index)
        self.view.update()


class PatternViewerView(QWidget):
    pattern_selected: SignalInstance = Signal(int)  # type: ignore

    PATTERNS = 256
    PATTERNS_PER_ROW = 16
    PATTERNS_PER_COLUMN = 16

    def __init__(
        self,
        parent: QWidget | None,
        graphics_set: GraphicsSet,
        palette_group: MutablePaletteGroup,
        palette_index: int,
        zoom: int = 4,
    ):
        super().__init__(parent)

        self.setMouseTracking(True)

        self.graphics_set = graphics_set
        self.palette_group = palette_group
        self.palette_index = palette_index
        self.zoom = zoom

    def resizeEvent(self, event: QResizeEvent):
        self.update()

    @property
    def zoom(self) -> int:
        return self._zoom

    @zoom.setter
    def zoom(self, value: int):
        self._zoom = value
        self.setFixedSize(
            self.PATTERNS_PER_ROW * Tile.WIDTH * self.zoom,  # type: ignore
            self.PATTERNS_PER_COLUMN * Tile.HEIGHT * self.zoom,  # type: ignore
        )

    @property
    def pattern_scale(self) -> int:
        return Tile.WIDTH * self.zoom  # type: ignore

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = Point.from_qpoint(event.pos())
        pos = pos // Point(self.pattern_scale, self.pattern_scale)

        dec_index = pos.y * self.PATTERNS_PER_ROW + pos.x
        hex_index = hex(dec_index).upper().replace("X", "x")

        status_message = f"Row: {pos.y}, Column: {pos.x}, Index: {dec_index} / {hex_index}"

        self.parent().statusBar().showMessage(status_message)  # type: ignore

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        pos = Point.from_qpoint(event.pos())
        pos = pos // Point(self.pattern_scale, self.pattern_scale)

        index = pos.y * self.PATTERNS_PER_ROW + pos.x
        self.pattern_selected.emit(index)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)

        bg_color = NESPalette[self.palette_group[self.palette_index][0]]
        painter.setBrush(QBrush(bg_color))
        painter.drawRect(QRect(QPoint(0, 0), self.size()))

        for i in range(self.PATTERNS):
            tile = Tile(
                i, tuple(tuple(c for c in pal) for pal in self.palette_group), self.palette_index, self.graphics_set
            )

            x = (i % self.PATTERNS_PER_ROW) * self.pattern_scale
            y = (i // self.PATTERNS_PER_ROW) * self.pattern_scale

            image = tile.as_image(self.pattern_scale)
            mask = image.createMaskFromColor(QColor(*MASK_COLOR).rgb(), Qt.MaskOutColor)
            image.setAlphaChannel(mask)
            painter.drawImage(x, y, image)
