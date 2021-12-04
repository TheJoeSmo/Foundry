from typing import Generic, Optional, TypeVar

from PySide6.QtCore import QMimeData, QSize, Qt, Signal, SignalInstance
from PySide6.QtGui import QDrag, QMouseEvent, QPainter, QPaintEvent
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from foundry.game.gfx.objects.EnemyItem import EnemyObject
from foundry.game.gfx.objects.LevelObject import LevelObject
from foundry.game.gfx.objects.LevelObjectFactory import LevelObjectFactory
from foundry.game.gfx.Palette import bg_color_for_palette_group
from foundry.gui.util import clear_layout

T = TypeVar("T", LevelObject, EnemyObject)


def get_minimal_icon_object(level_object: T) -> T:
    """
    Returns the object with a length, so that every block is rendered. E. g. clouds with length 0, don't have a face.
    """

    if not isinstance(level_object, LevelObject):
        return level_object

    factory = LevelObjectFactory(
        level_object.object_set.number,
        level_object.graphics_set,
        0,
        [],
        vertical_level=False,
        size_minimal=True,
    )

    if level_object.obj_index >= 0x1F:
        obj = factory.from_properties(
            domain=level_object.domain,
            object_index=(level_object.obj_index // 0x10) * 0x10,
            x=0,
            y=0,
            length=None,
            index=0,
        )
    else:
        obj = factory.from_properties(
            domain=level_object.domain, object_index=level_object.obj_index, x=0, y=0, length=None, index=0
        )
    if not isinstance(obj, LevelObject):
        return level_object

    obj.ground_level = 3

    while any(block not in obj.rendered_blocks for block in obj.blocks) and obj.length < 0x10:
        obj.length += 1

        if obj.is_4byte:
            obj.secondary_length += 1

        obj.render()

    return obj


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


class ObjectViewer(QWidget):
    def __init__(self, parent: Optional[QWidget], icon: Optional[ObjectButton] = None):
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
    def icon(self) -> Optional[ObjectButton]:
        return self._icon

    @icon.setter
    def icon(self, icon: Optional[ObjectButton]):
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
