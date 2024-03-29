from PySide6.QtCore import QPoint, QSize
from PySide6.QtGui import QCloseEvent, QColor, QImage, QPainter, QPaintEvent, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLayout,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from foundry.core.drawable import BLOCK_SIZE, MASK_COLOR, Block, block_to_image
from foundry.core.geometry import Point
from foundry.core.graphics_set.util import GRAPHIC_SET_NAMES
from foundry.game.File import ROM
from foundry.game.gfx.objects.Jump import Jump
from foundry.game.gfx.objects.LevelObject import LevelObject
from foundry.game.gfx.objects.LevelObjectFactory import LevelObjectFactory
from foundry.gui.CustomChildWindow import CustomChildWindow
from foundry.gui.LevelSelector import TILESET_ITEMS
from foundry.gui.Spinner import Spinner
from foundry.gui.util import clear_layout

ID_SPIN_DOMAIN = 1
ID_SPIN_TYPE = 2
ID_SPIN_LENGTH = 3
ID_OBJECT_SET_DROPDOWN = 4
ID_GFX_SET_DROPDOWN = 5

MAX_DOMAIN = 7
MAX_TYPE = 0xFF
MAX_LENGTH = 0xFF


class ObjectViewer(CustomChildWindow):
    def __init__(self, parent):
        super().__init__(parent, title="Object Viewer")

        self.spin_domain = Spinner(self, MAX_DOMAIN)
        self.spin_domain.valueChanged.connect(self.on_spin)

        self.spin_type = Spinner(self, MAX_TYPE)
        self.spin_type.valueChanged.connect(self.on_spin)

        self.spin_length = Spinner(self, MAX_LENGTH)
        self.spin_length.setDisabled(True)
        self.spin_length.valueChanged.connect(self.on_spin)

        self.toolbar_ = QToolBar(self)

        self.toolbar_.addWidget(self.spin_domain)
        self.toolbar_.addWidget(self.spin_type)
        self.toolbar_.addWidget(self.spin_length)

        self.tileset_dropdown = QComboBox(self.toolbar_)
        self.tileset_dropdown.addItems(TILESET_ITEMS[1:])
        self.tileset_dropdown.setCurrentIndex(0)

        self.graphic_set_dropdown = QComboBox(self.toolbar_)
        self.graphic_set_dropdown.addItems(GRAPHIC_SET_NAMES)
        self.graphic_set_dropdown.setCurrentIndex(1)

        self.tileset_dropdown.currentIndexChanged.connect(self.on_tileset)
        self.graphic_set_dropdown.currentIndexChanged.connect(self.on_graphic_set)

        self.toolbar_.addWidget(self.tileset_dropdown)
        self.toolbar_.addWidget(self.graphic_set_dropdown)

        self.addToolBar(self.toolbar_)

        self.drawing_area = ObjectDrawArea(self, 1)

        self.status_bar = QStatusBar(parent=self)
        self.status_bar.showMessage(self.drawing_area.current_object.name)

        self.setStatusBar(self.status_bar)

        self.drawing_area.update()

        self.block_list = BlockArray(self, self.drawing_area.current_object)

        central_widget = QWidget()
        central_widget.setLayout(QVBoxLayout())
        central_widget.layout().addWidget(self.drawing_area)
        central_widget.layout().addWidget(self.block_list)

        self.setCentralWidget(central_widget)

        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        return

    def closeEvent(self, event: QCloseEvent):
        self.toolbar_.close()
        super().closeEvent(event)

    def set_object_and_graphic_set(self, tileset: int, graphics_set: int):
        self.tileset_dropdown.setCurrentIndex(tileset - 1)
        self.graphic_set_dropdown.setCurrentIndex(graphics_set)

        self.drawing_area.change_tileset(tileset)
        self.drawing_area.change_graphic_set(graphics_set)

        self.block_list.update_object(self.drawing_area.current_object)
        self.status_bar.showMessage(self.drawing_area.current_object.name)

    def on_tileset(self):
        tileset = self.tileset_dropdown.currentIndex() + 1
        graphics_set = tileset

        self.set_object_and_graphic_set(tileset, graphics_set)

    def on_graphic_set(self):
        tileset = self.tileset_dropdown.currentIndex() + 1
        graphics_set = self.graphic_set_dropdown.currentIndex()

        self.set_object_and_graphic_set(tileset, graphics_set)

    def set_object(self, domain: int, obj_index: int, secondary_length: int):
        object_data = bytearray(4)

        object_data[0] = domain << 5
        object_data[1] = 0
        object_data[2] = obj_index
        object_data[3] = secondary_length

        self.spin_domain.setValue(domain)
        self.spin_type.setValue(obj_index)
        self.spin_length.setValue(secondary_length)

        self.drawing_area.update_object(object_data)
        self.block_list.update_object(self.drawing_area.current_object)

        if self.drawing_area.current_object.is_4byte:
            self.spin_length.setEnabled(True)
        else:
            self.spin_length.setValue(0)
            self.spin_length.setEnabled(False)

        self.drawing_area.update()

        self.status_bar.showMessage(self.drawing_area.current_object.name)

    def on_spin(self, _):
        domain = self.spin_domain.value()
        obj_index = self.spin_type.value()
        secondary_length = self.spin_length.value()

        self.set_object(domain, obj_index, secondary_length)


class ObjectDrawArea(QWidget):
    def __init__(self, parent, tileset, graphic_set=1, palette_index=0):
        super().__init__(parent)

        self.object_factory = LevelObjectFactory(tileset, graphic_set, palette_index, [], False, size_minimal=True)

        self.current_object = self.object_factory.from_data(bytearray([0x0, 0x0, 0x0]), 0)

        self.update_object()

        self.resize(QSize())

    def change_tileset(self, tileset: int):
        self.object_factory.set_tileset(tileset)

        self.update_object()

    def change_graphic_set(self, graphic_set: int):
        self.object_factory.set_graphic_set(graphic_set)
        self.update_object()

    def resize(self, size: QSize):
        if isinstance(self.current_object, Jump):
            return

        self.setMinimumSize((self.current_object.rendered_size * BLOCK_SIZE).to_qt())

    def update_object(self, object_data: bytearray | LevelObject | Jump | None = None):
        if object_data is None:
            object_data = self.current_object.data
        elif isinstance(object_data, (LevelObject, Jump)):
            object_data = object_data.data

        self.current_object = self.object_factory.from_data(object_data, 0)

        self.resize(QSize())
        self.update()

    def paintEvent(self, event: QPaintEvent):
        if not isinstance(self.current_object, LevelObject):
            return

        painter = QPainter(self)
        painter.translate((self.current_object.rendered_position * BLOCK_SIZE * -1).to_qt())
        self.current_object.draw(painter, BLOCK_SIZE.width, transparent=True)


class BlockArray(QWidget):
    def __init__(self, parent, level_object: LevelObject):
        super().__init__(parent)

        self.setLayout(QHBoxLayout())

        self.setContentsMargins(0, 0, 0, 0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        self.level_object = level_object

        self.update_object(level_object)

    def update_object(self, level_object: LevelObject):
        self.level_object = level_object

        clear_layout(self.layout())

        for block_index in self.level_object.blocks:
            normalized_index: int = block_index if block_index <= 0xFF else ROM().get_byte(block_index)
            image = block_to_image(
                Block.from_tsa(Point(0, 0), normalized_index, self.level_object.tsa_data),
                self.level_object.palette_group,
                self.level_object.graphics_set,
                BLOCK_SIZE.width,
            ).copy()
            mask: QImage = image.createMaskFromColor(QColor(*MASK_COLOR).rgb(), Qt.MaskMode.MaskOutColor)
            image.setAlphaChannel(mask)
            self.layout().addWidget(
                BlockArea(
                    image,
                    normalized_index,
                )
            )

        self.update()


class BlockArea(QWidget):
    def __init__(self, image: QImage, index: int) -> None:
        super().__init__()
        self.image = image
        self.setContentsMargins(0, 0, 0, 0)
        self.setToolTip(hex(index))

    def sizeHint(self) -> QSize:
        return BLOCK_SIZE.to_qt()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.drawImage(QPoint(0, 0), self.image)
        painter.end()
