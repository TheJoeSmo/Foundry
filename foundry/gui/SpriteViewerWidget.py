from PySide6.QtCore import QSize, Qt, Signal, SignalInstance
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent
from PySide6.QtWidgets import QFrame, QSizePolicy, QWidget

from foundry.core.graphics_set.GraphicsSet import GraphicsSetProtocol
from foundry.core.palette.PaletteGroup import MutablePaletteGroupProtocol
from foundry.core.sprites import SPRITE_SIZE
from foundry.core.sprites.Sprite import SpriteProtocol
from foundry.core.sprites.SpriteGroup import SpriteGroupProtocol
from foundry.game.gfx.drawable import MASK_COLOR


class SpriteViewerWidget(QFrame):
    sprites_changed: SignalInstance = Signal(list[SpriteProtocol])  # type: ignore
    graphics_set_changed: SignalInstance = Signal(GraphicsSetProtocol)  # type: ignore
    palette_group_changed: SignalInstance = Signal(MutablePaletteGroupProtocol)  # type: ignore
    transparency_changed: SignalInstance = Signal(bool)  # type: ignore
    zoom_changed: SignalInstance = Signal(int)  # type: ignore
    mouse_moved_over_widget: SignalInstance = Signal(QMouseEvent)  # type: ignore
    clicked: SignalInstance = Signal(int, int)  # type: ignore

    def __init__(
        self, parent: QWidget | None, sprite_group: SpriteGroupProtocol, zoom: int = 2, transparent: bool = True
    ):
        super().__init__(parent)

        self.setMouseTracking(True)

        self.sprite_group = sprite_group
        self._transparent = transparent
        self.zoom = zoom

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    @property
    def sprites(self) -> list[SpriteProtocol]:
        return self.sprite_group.sprites

    @sprites.setter
    def sprites(self, sprites: list[SpriteProtocol]):
        self.sprite_group.sprites = sprites
        self.sprites_changed.emit(sprites)
        self.update()

    @property
    def graphics_set(self) -> GraphicsSetProtocol:
        return self.sprite_group.graphics_set

    @graphics_set.setter
    def graphics_set(self, graphics_set: GraphicsSetProtocol):
        self.sprite_group.graphics_set = graphics_set
        self.graphics_set_changed.emit(graphics_set)
        self.update()

    @property
    def palette_group(self) -> MutablePaletteGroupProtocol:
        return self.sprite_group.palette_group

    @palette_group.setter
    def palette_group(self, palette_group: MutablePaletteGroupProtocol):
        self.sprite_group.palette_group = palette_group
        self.palette_group_changed.emit(palette_group)
        self.update()

    @property
    def transparent(self) -> bool:
        return self._transparent

    @transparent.setter
    def transparent(self, transparent: bool):
        self._transparent = transparent
        self.transparency_changed.emit(transparent)
        self.update()

    @property
    def zoom(self) -> int:
        return self._zoom

    @zoom.setter
    def zoom(self, zoom: int):
        self._zoom = zoom
        self.setFixedSize(self.sizeHint())
        self.zoom_changed.emit(zoom)
        self.update()

    def sizeHint(self):
        return QSize(self.sprite_group.size.width * self.zoom, self.sprite_group.size.height * self.zoom)

    def mouseMoveEvent(self, event: QMouseEvent):
        self.mouse_moved_over_widget.emit(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        x, y = event.x() // (self.zoom * SPRITE_SIZE.width), event.y() // (self.zoom * SPRITE_SIZE.height)
        self.clicked.emit(x, y)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)

        image = self.sprite_group.image(self.zoom)
        if self.transparent:
            mask = image.createMaskFromColor(QColor(*MASK_COLOR).rgb(), Qt.MaskOutColor)
            image.setAlphaChannel(mask)

        painter.drawImage(0, 0, image)

        return super().paintEvent(event)
