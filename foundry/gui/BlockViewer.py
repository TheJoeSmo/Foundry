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
from foundry.core.Position import Position
from foundry.game.File import ROM
from foundry.game.gfx.drawable.Block import Block
from foundry.game.gfx.GraphicsSet import GraphicsSet
from foundry.game.gfx.Palette import (
    PALETTE_GROUPS_PER_OBJECT_SET,
    bg_color_for_object_set,
    load_palette_group,
)
from foundry.gui.CustomChildWindow import CustomChildWindow
from foundry.gui.LevelSelector import OBJECT_SET_ITEMS
from foundry.gui.Spinner import Spinner


@attrs(slots=True, auto_attribs=True)
class BlockViewerModel:
    tileset: int
    palette_group: int


class BlockViewerController(CustomChildWindow):
    tileset_changed: SignalInstance = Signal(int)  # type: ignore
    palette_group_changed: SignalInstance = Signal(int)  # type: ignore

    def __init__(self, parent):
        super().__init__(parent, "Block Viewer")

        self.model = BlockViewerModel(0, 0)
        self.view = BlockViewerView(parent=self)
        self.setCentralWidget(self.view)
        self.toolbar = QToolBar(self)

        self.prev_os_action = self.toolbar.addAction(icon("arrow-left.svg"), "Previous object set")
        self.next_os_action = self.toolbar.addAction(icon("arrow-right.svg"), "Next object set")
        self.zoom_out_action = self.toolbar.addAction(icon("zoom-out.svg"), "Zoom Out")
        self.zoom_in_action = self.toolbar.addAction(icon("zoom-in.svg"), "Zoom In")

        def change_tileset(offset: int):
            self.tileset += offset

        def change_zoom(offset: int):
            self.view.zoom += offset

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
        self.toolbar.addWidget(QLabel(" Object Palette: "))
        self.toolbar.addWidget(self.palette_group_spinner)

        self.addToolBar(self.toolbar)

        self.layout().setSizeConstraint(QLayout.SetFixedSize)

        self.setStatusBar(QStatusBar(self))

    def closeEvent(self, event: QCloseEvent):
        self.toolbar.close()
        super().closeEvent(event)

    @property
    def tileset(self) -> int:
        return self.model.tileset

    @tileset.setter
    def tileset(self, value: int):
        self.model.tileset = min(max(value, 0), 0xE)
        self.view.object_set = self.tileset
        self.tileset_changed.emit(self.tileset)
        self.view.update()

    @property
    def palette_group(self) -> int:
        return self.model.palette_group

    @palette_group.setter
    def palette_group(self, value: int):
        self.model.palette_group = value
        self.view.palette_group = value
        self.palette_group_changed.emit(self.palette_group)
        self.view.update()


class BlockViewerView(QWidget):
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
        pos = Position.from_qpoint(event.pos())
        pos.x, pos.y = pos.x // self.block_scale, pos.y // self.block_scale

        dec_index = pos.y * self.BLOCKS_PER_ROW + pos.x
        hex_index = hex(dec_index).upper().replace("X", "x")

        status_message = f"Row: {pos.y}, Column: {pos.x}, Index: {dec_index} / {hex_index}"

        self.parent().statusBar().showMessage(status_message)  # type: ignore

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)

        bg_color = bg_color_for_object_set(self.object_set, 0)
        painter.setBrush(QBrush(bg_color))

        painter.drawRect(QRect(QPoint(0, 0), self.size()))

        graphics_set = GraphicsSet.from_tileset(self.object_set)
        palette = load_palette_group(self.object_set, self.palette_group)
        tsa_data = ROM.get_tsa_data(self.object_set)

        for i in range(self.BLOCKS):
            block = Block(i, palette, graphics_set, tsa_data)

            x = (i % self.BLOCKS_PER_ROW) * self.block_scale
            y = (i // self.BLOCKS_PER_ROW) * self.block_scale

            block.draw(painter, x, y, self.block_scale)
