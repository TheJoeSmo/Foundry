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
from PySide6.QtWidgets import QComboBox, QLabel, QLayout, QStatusBar, QToolBar, QWidget

from foundry import icon
from foundry.core.geometry import Point
from foundry.core.graphics_set.GraphicsSet import GraphicsSet
from foundry.core.palette import PALETTE_GROUPS_PER_OBJECT_SET
from foundry.core.palette.PaletteGroup import MutablePaletteGroup
from foundry.core.UndoController import UndoController
from foundry.game.File import ROM
from foundry.game.gfx.drawable.Block import Block
from foundry.gui.BlockEditor import BlockEditorController as BlockEditor
from foundry.gui.CustomChildWindow import CustomChildWindow
from foundry.gui.LevelSelector import OBJECT_SET_ITEMS
from foundry.gui.Spinner import Spinner


@attrs(slots=True, auto_attribs=True)
class BlockViewerModel:
    tileset: int
    palette_group: int


class BlockViewerController(CustomChildWindow):
    tile_square_assembly_changed: SignalInstance = Signal(bytearray)  # type: ignore
    tileset_changed: SignalInstance = Signal(int)  # type: ignore
    palette_group_changed: SignalInstance = Signal(int)  # type: ignore
    destroyed: SignalInstance = Signal()  # type: ignore

    def __init__(self, parent):
        super().__init__(parent, "Block Viewer")

        self.model = BlockViewerModel(0, 0)
        self.view = BlockViewerView(parent=self)
        self.undo_controller = UndoController(ROM.get_tsa_data(self.tileset))
        self.setCentralWidget(self.view)
        self.toolbar = QToolBar(self)
        self.editor = None

        self.view.block_selected.connect(self._on_block_selected)
        self.view.destroyed.connect(self.destroy)  # type: ignore

        self.undo_action = self.toolbar.addAction(icon("rotate-ccw.png"), "Undo Action")
        self.redo_action = self.toolbar.addAction(icon("rotate-cw.png"), "Redo Action")
        self.prev_os_action = self.toolbar.addAction(icon("arrow-left.png"), "Previous object set")
        self.next_os_action = self.toolbar.addAction(icon("arrow-right.png"), "Next object set")
        self.zoom_out_action = self.toolbar.addAction(icon("zoom-out.png"), "Zoom Out")
        self.zoom_in_action = self.toolbar.addAction(icon("zoom-in.png"), "Zoom In")

        def change_tileset(offset: int):
            self.tileset += offset

        def change_zoom(offset: int):
            self.view.zoom += offset

        def undo(*_):
            self.undo_controller.undo()
            self._update_tsa_data()

        def redo(*_):
            self.undo_controller.redo()
            self._update_tsa_data()

        self.undo_action.triggered.connect(undo)  # type: ignore
        self.undo_action.setEnabled(False)
        self.redo_action.triggered.connect(redo)  # type: ignore
        self.redo_action.setEnabled(False)
        self.prev_os_action.triggered.connect(lambda *_: change_tileset(-1))  # type: ignore
        self.next_os_action.triggered.connect(lambda *_: change_tileset(1))  # type: ignore
        self.zoom_out_action.triggered.connect(lambda *_: change_zoom(-1))  # type: ignore
        self.zoom_in_action.triggered.connect(lambda *_: change_zoom(1))  # type: ignore

        def on_combo(*_):
            self.tileset = self.bank_dropdown.currentIndex()

        self.bank_dropdown = QComboBox(parent=self.toolbar)
        self.bank_dropdown.addItems(OBJECT_SET_ITEMS)
        self.bank_dropdown.setCurrentIndex(0)
        self.bank_dropdown.currentIndexChanged.connect(on_combo)  # type: ignore
        self.tileset_changed.connect(self.bank_dropdown.setCurrentIndex)

        def on_palette(value):
            self.palette_group = value

        self.palette_group_spinner = Spinner(self, maximum=PALETTE_GROUPS_PER_OBJECT_SET - 1, base=10)
        self.palette_group_spinner.valueChanged.connect(on_palette)  # type: ignore
        self.palette_group_changed.connect(self.palette_group_spinner.setValue)

        self.toolbar.addWidget(self.bank_dropdown)
        self.toolbar.addWidget(QLabel(" Object palette: "))
        self.toolbar.addWidget(self.palette_group_spinner)

        self.addToolBar(self.toolbar)

        self.layout().setSizeConstraint(QLayout.SetFixedSize)

        self.setStatusBar(QStatusBar(self))

    def closeEvent(self, event: QCloseEvent):
        self.toolbar.close()
        if self.editor is not None:
            self.editor.close()
        self.destroyed.emit()
        super().closeEvent(event)

    @property
    def tsa_data(self) -> bytearray:
        return self.undo_controller.state

    @tsa_data.setter
    def tsa_data(self, tsa_data: bytearray):
        self.undo_controller.do(tsa_data)
        self._update_tsa_data()

    def _update_tsa_data(self):
        ROM.write_tsa_data(self.tileset, self.tsa_data)
        Block.clear_cache()
        self.undo_action.setEnabled(self.undo_controller.can_undo)
        self.redo_action.setEnabled(self.undo_controller.can_redo)
        self.tile_square_assembly_changed.emit(self.tsa_data)
        self.view.update()

    @property
    def tileset(self) -> int:
        return self.model.tileset

    @tileset.setter
    def tileset(self, value: int):
        self.model.tileset = min(max(value, 0), 0xE)
        self.undo_controller = UndoController(ROM.get_tsa_data(self.tileset))
        self.view.object_set = self.tileset
        self.tileset_changed.emit(self.tileset)
        self.view.update()
        if self.editor is not None:
            self.editor.silent_update_tsa_data(self.tsa_data)
            self.editor.palette_group = MutablePaletteGroup.from_tileset(self.tileset, self.palette_group)
            self.editor.graphics_set = GraphicsSet.from_tileset(self.tileset)

    @property
    def palette_group(self) -> int:
        return self.model.palette_group

    @palette_group.setter
    def palette_group(self, value: int):
        self.model.palette_group = value
        self.view.palette_group = value
        self.palette_group_changed.emit(self.palette_group)
        self.view.update()
        if self.editor is not None:
            self.editor.palette_group = MutablePaletteGroup.from_tileset(self.tileset, value)

    def _on_block_selected(self, index: int):
        if self.editor is None:
            self.editor = BlockEditor(
                self,
                ROM.get_tsa_data(self.tileset),
                index,
                GraphicsSet.from_tileset(self.tileset),
                MutablePaletteGroup.from_tileset(self.tileset, self.palette_group),
                index // 0x40,
            )

            def change_tsa_data(tsa_data: bytearray):
                self.tsa_data = tsa_data

            def remove_editor(*_):
                self.editor = None

            self.editor.tile_square_assembly_changed.connect(change_tsa_data)
            self.editor.destroyed.connect(remove_editor)
            self.tile_square_assembly_changed.connect(self.editor.silent_update_tsa_data)
            self.editor.show()
        else:
            self.editor.block_index = index


class BlockViewerView(QWidget):
    block_selected: SignalInstance = Signal(int)  # type: ignore

    BLOCKS = 256
    BLOCKS_PER_ROW = 16
    BLOCKS_PER_COLUMN = 16

    def __init__(self, parent, object_set=0, palette_group=0, zoom=2):
        super().__init__(parent)

        self.setMouseTracking(True)

        self.object_set = object_set
        self.palette_group = palette_group
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
            self.BLOCKS_PER_ROW * Block.WIDTH * self.zoom, self.BLOCKS_PER_COLUMN * Block.HEIGHT * self.zoom
        )

    @property
    def block_scale(self) -> int:
        return Block.WIDTH * self.zoom

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = Point.from_qpoint(event.pos())
        pos = pos // Point(self.block_scale, self.block_scale)

        dec_index = pos.y * self.BLOCKS_PER_ROW + pos.x
        hex_index = hex(dec_index).upper().replace("X", "x")

        status_message = f"Row: {pos.y}, Column: {pos.x}, Index: {dec_index} / {hex_index}"

        self.parent().statusBar().showMessage(status_message)  # type: ignore

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        pos = Point.from_qpoint(event.pos())
        pos = pos // Point(self.block_scale, self.block_scale)

        index = pos.y * self.BLOCKS_PER_ROW + pos.x
        self.block_selected.emit(index)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)

        palette = MutablePaletteGroup.from_tileset(self.object_set, self.palette_group)
        frozen_palette = tuple(tuple(c for c in pal) for pal in palette)
        bg_color = palette.background_color
        painter.setBrush(QBrush(bg_color))

        painter.drawRect(QRect(QPoint(0, 0), self.size()))

        graphics_set = GraphicsSet.from_tileset(self.object_set)
        tsa_data = ROM.get_tsa_data(self.object_set)

        for i in range(self.BLOCKS):
            block = Block(i, frozen_palette, graphics_set, tsa_data)

            x = (i % self.BLOCKS_PER_ROW) * self.block_scale
            y = (i // self.BLOCKS_PER_ROW) * self.block_scale

            block.draw(painter, x, y, self.block_scale)
