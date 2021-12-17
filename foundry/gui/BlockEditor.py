from typing import Optional

from attr import attrs
from PySide6.QtCore import QPoint, QRect, Signal, SignalInstance
from PySide6.QtGui import (
    QBrush,
    QCloseEvent,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QResizeEvent,
)
from PySide6.QtWidgets import QLayout, QStatusBar, QToolBar, QWidget

from foundry import icon
from foundry.core.Position import Position
from foundry.game.gfx.drawable.Block import Block
from foundry.game.gfx.GraphicsSet import GraphicsSet
from foundry.game.gfx.Palette import PaletteGroup
from foundry.gui.CustomChildWindow import CustomChildWindow
from foundry.gui.PatternViewer import PatternViewerController as PatternViewer


@attrs(slots=True, auto_attribs=True)
class BlockEditorModel:
    tile_square_assembly: bytearray
    block_index: int
    graphics_set: GraphicsSet
    palette_group: PaletteGroup
    palette_index: int


class BlockEditorController(CustomChildWindow):
    tile_square_assembly_changed: SignalInstance = Signal(bytearray)  # type: ignore
    block_index_changed: SignalInstance = Signal(int)  # type: ignore
    graphics_set_changed: SignalInstance = Signal(GraphicsSet)  # type: ignore
    palette_group_changed: SignalInstance = Signal(PaletteGroup)  # type: ignore
    palette_index_changed: SignalInstance = Signal(int)  # type: ignore

    def __init__(
        self,
        parent: Optional[QWidget],
        tsa_data: bytearray,
        block_index: int,
        graphics_set: GraphicsSet,
        palette_group: PaletteGroup,
        palette_index: int,
    ):
        super().__init__(parent, "Block Editor")

        self.model = BlockEditorModel(tsa_data, block_index, graphics_set, palette_group, palette_index)
        self.view = BlockEditorView(self, tsa_data, block_index, graphics_set, palette_group, palette_index)
        self.setCentralWidget(self.view)
        self.toolbar = QToolBar(self)

        self.view.block_pattern_change.connect(lambda values: self._on_block_pattern_change(*values))

        self.zoom_out_action = self.toolbar.addAction(icon("zoom-out.svg"), "Zoom Out")
        self.zoom_in_action = self.toolbar.addAction(icon("zoom-in.svg"), "Zoom In")

        def change_zoom(offset: int):
            self.view.zoom += offset

        self.zoom_out_action.triggered.connect(lambda *_: change_zoom(-1))  # type: ignore
        self.zoom_in_action.triggered.connect(lambda *_: change_zoom(1))  # type: ignore

        self.addToolBar(self.toolbar)
        self.setStatusBar(QStatusBar(self))

        self.layout().setSizeConstraint(QLayout.SetFixedSize)

    def closeEvent(self, event: QCloseEvent):
        self.toolbar.close()
        super().closeEvent(event)

    @property
    def tsa_data(self) -> bytearray:
        return self.model.tile_square_assembly

    @tsa_data.setter
    def tsa_data(self, value: bytearray):
        self.model.tile_square_assembly = value
        self.view.tsa_data = self.tsa_data
        self.tile_square_assembly_changed.emit(self.tsa_data)
        self.view.update()

    @property
    def block_index(self) -> int:
        return self.model.block_index

    @block_index.setter
    def block_index(self, value: int):
        self.model.block_index = value
        self.view.block_index = value
        self.graphics_set_changed.emit(self.block_index)
        self.view.update()

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
    def palette_group(self) -> PaletteGroup:
        return self.model.palette_group

    @palette_group.setter
    def palette_group(self, value: PaletteGroup):
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

    def _on_block_pattern_change(self, x: int, y: int, pattern: int):
        index = self.block_index + 0x100 * (x * 2 + y)
        tsa_data = self.tsa_data
        tsa_data[index] = pattern
        self.tsa_data = tsa_data


class BlockEditorView(QWidget):
    block_pattern_change: SignalInstance = Signal(object)  # type: ignore

    def __init__(
        self,
        parent: Optional[QWidget],
        tsa_data: bytearray,
        block_index: int,
        graphics_set: GraphicsSet,
        palette_group: PaletteGroup,
        palette_index: int,
        zoom: int = 16,
    ):
        super().__init__(parent)

        self.tsa_data = tsa_data
        self.block_index = block_index
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
        self.setFixedSize(self.block_scale, self.block_scale)

    @property
    def block_scale(self) -> int:
        return Block.WIDTH * self.zoom

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        pos = Position.from_qpoint(event.pos())
        pos.x, pos.y = pos.x // (self.block_scale // 2), pos.y // (self.block_scale // 2)

        pattern_viewer = PatternViewer(self, self.graphics_set, self.palette_group, self.block_index // 0x40)
        pattern_viewer.pattern_selected.connect(lambda ptn: self.block_pattern_change.emit((pos.x, pos.y, ptn)))
        pattern_viewer.show()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)

        bg_color = self.palette_group[0][0]
        painter.setBrush(QBrush(bg_color))
        painter.drawRect(QRect(QPoint(0, 0), self.size()))
        block = Block(self.block_index, self.palette_group, self.graphics_set, self.tsa_data)
        block.draw(painter, 0, 0, self.block_scale)