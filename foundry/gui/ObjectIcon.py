from typing import Generic, Optional, TypeVar

from PySide6.QtCore import QMimeData, QSize, Qt, Signal, SignalInstance
from PySide6.QtGui import QDrag, QMouseEvent, QPainter, QPaintEvent
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from foundry.game.gfx.objects.EnemyItem import EnemyObject
from foundry.game.gfx.objects.LevelObject import LevelObject
from foundry.game.gfx.Palette import bg_color_for_palette_group
from foundry.gui.util import clear_layout

T = TypeVar("T", LevelObject, EnemyObject)


def get_minimal_icon_object(level_object: T) -> T:
    """
    Returns the object with a length, so that every block is rendered. E. g. clouds with length 0, don't have a face.
    """

    if isinstance(level_object, EnemyObject):
        return level_object

    level_object.ground_level = 3

    while (
        any(block not in level_object.rendered_blocks for block in level_object.blocks) and level_object.length < 0x10
    ):
        level_object.length += 1

        if level_object.is_4byte:
            level_object.secondary_length += 1

        level_object.render()

    return level_object


class ObjectIcon(QWidget, Generic[T]):
    def __init__(
        self,
        parent: Optional[QWidget],
        item: T,
        background_color: bool = True,
    ):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._item = item
        self.setToolTip(self.item.name)
        self._background_color = background_color

    @property
    def item(self) -> T:
        return self._item

    @item.setter
    def item(self, item: T):
        self._item = item
        self.setToolTip(item.name)
        self.update()

    @property
    def background_color(self) -> bool:
        return self._background_color

    @background_color.setter
    def background_color(self, background_color: bool):
        if self._background_color != background_color:
            self._background_color = background_color
            self.update()

    def sizeHint(self):
        return QSize(32, 32)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)

        if self.background_color:
            painter.fillRect(event.rect(), bg_color_for_palette_group(self.item.palette_group))

        scaled_image = get_minimal_icon_object(self.item).as_image().scaled(self.size(), aspectMode=Qt.KeepAspectRatio)

        x = (self.width() - scaled_image.width()) // 2
        y = (self.height() - scaled_image.height()) // 2

        painter.drawImage(x, y, scaled_image)

        return super(ObjectIcon, self).paintEvent(event)


class ObjectViewer(QWidget):
    def __init__(self, parent: Optional[QWidget], icon: Optional[ObjectIcon] = None):
        super().__init__(parent)
        self.icon = icon
        self.layout_ = QVBoxLayout()
        self.setLayout(self.layout_)
        self.setWhatsThis(
            "<b>Current Object</b><br/>"
            "Shows the currently selected object and its name. It can be placed by "
            "clicking the middle mouse button anywhere in the level."
        )

    @property
    def icon(self) -> Optional[ObjectIcon]:
        return self._icon

    @icon.setter
    def icon(self, icon: Optional[ObjectIcon]):
        self._icon = icon
        if icon is not None:
            clear_layout(self.layout_)
            icon.setFixedSize(QSize(64, 64))
            name = QLabel(icon.item.name)
            name.setWordWrap(True)
            name.setAlignment(Qt.AlignCenter)
            name.setContentsMargins(0, 0, 0, 0)
            self.layout_.addWidget(icon)
            self.layout_.addWidget(name)


class ObjectButton(ObjectIcon):
    selected: SignalInstance = Signal()  # type: ignore
    object_created: SignalInstance = Signal()  # type: ignore

    def mouseMoveEvent(self, event: QMouseEvent):
        if not (event.buttons() & Qt.LeftButton):
            return super().mouseMoveEvent(event)

        drag_event = QDrag(self)
        mime_data = QMimeData()
        object_bytes = bytearray()
        object_bytes.append(0 if isinstance(self.item, LevelObject) else 1)
        object_bytes.extend(self.item.to_bytes())
        mime_data.setData("application/level-object", object_bytes)
        drag_event.setMimeData(mime_data)

        if drag_event.exec_() == Qt.MoveAction:
            self.object_created.emit()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.selected.emit()

        return super().mouseReleaseEvent(event)
