from math import ceil

from attr import attrs
from PySide6.QtCore import QPoint, QRect, QSize, Signal, SignalInstance
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
        self.view = BlockBank(parent=self)
        self.setCentralWidget(self.view)
        self.toolbar = QToolBar(self)

        self.prev_os_action = self.toolbar.addAction(icon("arrow-left.svg"), "Previous object set")
        self.next_os_action = self.toolbar.addAction(icon("arrow-right.svg"), "Next object set")
        self.zoom_out_action = self.toolbar.addAction(icon("zoom-out.svg"), "Zoom Out")
        self.zoom_in_action = self.toolbar.addAction(icon("zoom-in.svg"), "Zoom In")

        def change_tileset(offset: int):
            self.tileset += offset

        self.prev_os_action.triggered.connect(lambda *_: change_tileset(-1))  # type: ignore
        self.next_os_action.triggered.connect(lambda *_: change_tileset(1))  # type: ignore
        self.zoom_out_action.triggered.connect(self.view.zoom_out)  # type: ignore
        self.zoom_in_action.triggered.connect(self.view.zoom_in)  # type: ignore

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


class BlockBank(QWidget):
    def __init__(self, parent, object_set=0, palette_group=0, zoom=2):
        super(BlockBank, self).__init__(parent)
        self.setMouseTracking(True)

        self.sprites = 256
        self.zoom_step = 256
        self.sprites_horiz = 16
        self.sprites_vert = ceil(self.sprites / self.sprites_horiz)

        self.object_set = object_set
        self.palette_group = palette_group
        self.zoom = zoom

        self._size = QSize(self.sprites_horiz * Block.WIDTH * self.zoom, self.sprites_vert * Block.HEIGHT * self.zoom)

        self.setFixedSize(self._size)

    def resizeEvent(self, event: QResizeEvent):
        self.update()

    def zoom_in(self):
        self.zoom += 1
        self._after_zoom()

    def zoom_out(self):
        self.zoom = max(self.zoom - 1, 1)
        self._after_zoom()

    def _after_zoom(self):
        new_size = QSize(self.sprites_horiz * Block.WIDTH * self.zoom, self.sprites_vert * Block.HEIGHT * self.zoom)

        self.setFixedSize(new_size)

    def mouseMoveEvent(self, event: QMouseEvent):
        x, y = event.pos().toTuple()

        block_length = Block.WIDTH * self.zoom

        column = x // block_length
        row = y // block_length

        dec_index = row * self.sprites_horiz + column
        hex_index = hex(dec_index).upper().replace("X", "x")

        status_message = f"Row: {row}, Column: {column}, Index: {dec_index} / {hex_index}"

        self.parent().statusBar().showMessage(status_message)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)

        bg_color = bg_color_for_object_set(self.object_set, 0)
        painter.setBrush(QBrush(bg_color))

        painter.drawRect(QRect(QPoint(0, 0), self.size()))

        graphics_set = GraphicsSet.from_tileset(self.object_set)
        palette = load_palette_group(self.object_set, self.palette_group)
        tsa_data = ROM.get_tsa_data(self.object_set)

        horizontal = self.sprites_horiz

        block_length = Block.WIDTH * self.zoom

        for i in range(self.sprites):
            block = Block(i, palette, graphics_set, tsa_data)

            x = (i % horizontal) * block_length
            y = (i // horizontal) * block_length

            block.draw(painter, x, y, block_length)

        return
