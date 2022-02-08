from typing import Optional

from attr import attrs
from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QHBoxLayout, QLayout, QStatusBar, QToolBar, QWidget

from foundry import icon
from foundry.core.palette.PaletteGroup import MutablePaletteGroupProtocol
from foundry.core.player_animations import ANIMATION_WIDTH
from foundry.core.player_animations.PlayerAnimation import PlayerAnimation
from foundry.core.player_animations.util import (
    get_animations_palette_index,
    load_player_animation,
)
from foundry.core.point.Point import MutablePoint
from foundry.core.sprites import SPRITE_SIZE
from foundry.core.sprites.Sprite import Sprite, SpriteProtocol
from foundry.core.sprites.SpriteGroup import SpriteGroup, SpriteGroupProtocol
from foundry.gui.CustomChildWindow import CustomChildWindow
from foundry.gui.Spinner import Spinner
from foundry.gui.SpriteViewer import SpriteViewerController as SpriteViewer
from foundry.gui.SpriteViewerWidget import SpriteViewerWidget


@attrs(slots=True, auto_attribs=True)
class PlayerFrameEditorModel:
    animation: PlayerAnimation
    power_up_offsets: list[int]
    palette_group: MutablePaletteGroupProtocol
    is_mario: bool


class PlayerFrameEditorController(CustomChildWindow):
    frames_changed: SignalInstance = Signal(object)  # type: ignore
    offset_changed: SignalInstance = Signal(int)  # type: ignore
    destroyed: SignalInstance = Signal()  # type: ignore

    def __init__(
        self,
        parent: Optional[QWidget],
        animation: PlayerAnimation,
        power_up_offsets: list[int],
        palette_group: MutablePaletteGroupProtocol,
        is_mario: bool = True,
        title: str = "Player Frame Editor",
        zoom: int = 2,
    ):
        super().__init__(parent, title)

        self.model = PlayerFrameEditorModel(animation, power_up_offsets, palette_group, is_mario)
        self.view = PlayerFrameEditorView(self, self.sprite_groups, zoom)
        self.sprite_viewer: Optional[SpriteViewer] = None
        self.sprite_viewer_index = 0
        self.setCentralWidget(self.view)
        self.toolbar = QToolBar(self)

        self.toolbar.setMovable(False)

        self.view.clicked.connect(self._create_sprite_viewer)

        self.zoom_out_action = self.toolbar.addAction(icon("zoom-out.svg"), "Zoom Out")
        self.zoom_in_action = self.toolbar.addAction(icon("zoom-in.svg"), "Zoom In")

        self.page_offset_spinner = Spinner(self, 0xFF)
        self.page_offset_spinner.setValue(animation.offset)

        def change_zoom(offset: int):
            self.view.zoom += offset

        def change_page_offset(offset: int):
            self.page_offset = offset

        self.zoom_out_action.triggered.connect(lambda *_: change_zoom(-1))  # type: ignore
        self.zoom_in_action.triggered.connect(lambda *_: change_zoom(1))  # type: ignore

        self.page_offset_spinner.valueChanged.connect(change_page_offset)  # type: ignore

        self.toolbar.addWidget(self.page_offset_spinner)

        self.addToolBar(self.toolbar)

        self.setStatusBar(QStatusBar(self))
        self.layout().setSizeConstraint(QLayout.SetFixedSize)

    def closeEvent(self, event: QCloseEvent):
        self.toolbar.close()
        if self.sprite_viewer is not None:
            self.sprite_viewer.close()
        self.destroyed.emit()
        super().closeEvent(event)

    @property
    def is_mario(self) -> bool:
        return self.model.is_mario

    @is_mario.setter
    def is_mario(self, is_mario: bool):
        self.model.is_mario = is_mario
        self._update_view_animations()

    @property
    def power_up_offsets(self) -> list[int]:
        return self.model.power_up_offsets

    @power_up_offsets.setter
    def power_up_offsets(self, offsets: list[int]):
        self.model.power_up_offsets = offsets
        self._update_view_animations()

    @property
    def palette_group(self) -> MutablePaletteGroupProtocol:
        return self.model.palette_group

    @palette_group.setter
    def palette_group(self, palette_group: MutablePaletteGroupProtocol):
        self.model.palette_group = palette_group
        self._update_view_animations()

    @property
    def page_offset(self) -> int:
        return self.model.animation.offset

    @page_offset.setter
    def page_offset(self, offset: int):
        self.model.animation.offset = offset
        self.page_offset_spinner.setValue(offset)
        self.offset_changed.emit(offset)
        self._update_view_animations()

    @property
    def frame(self) -> bytearray:
        return self.model.animation.animations

    @frame.setter
    def frame(self, frame: bytearray):
        self.model.animation.animations = frame
        self.frames_changed.emit(frame)
        self._update_view_animations()

    @property
    def sprite_groups(self) -> list[SpriteGroupProtocol]:
        sprite_groups: list[SpriteGroupProtocol] = []

        for idx in range(len(self.model.power_up_offsets)):
            animation = load_player_animation(
                self.model.animation,
                self.model.palette_group,
                self.model.is_mario,
                idx,
                self.model.power_up_offsets,
            )
            sprites: list[SpriteProtocol] = []

            for idx, sprite in enumerate(animation.frames):
                sprites.append(
                    Sprite(
                        MutablePoint(
                            (idx % ANIMATION_WIDTH) * SPRITE_SIZE.width,
                            (idx // ANIMATION_WIDTH) * SPRITE_SIZE.height,
                        ),
                        sprite,
                        animation.palette_index,
                        animation.horizontal_flip[idx],
                        do_not_render=sprite == 0xF0,
                    )
                )

            sprite_groups.append(
                SpriteGroup(MutablePoint(0, 0), sprites, animation.graphics_set, animation.palette_group)
            )

        return sprite_groups

    def _update_view_animations(self):
        self.view.sprite_groups = self.sprite_groups
        self.page_offset_spinner.setValue(self.page_offset)
        self.view._update()

    def _create_sprite_viewer(self, positional_index: int, widget_index: int):
        self.sprite_viewer_index = positional_index

        if self.sprite_viewer is None:
            self.sprite_viewer = SpriteViewer(
                self,
                self.sprite_groups[widget_index].graphics_set,
                self.model.palette_group,
                get_animations_palette_index(self.model.is_mario, widget_index),
            )

            def remove_sprite_viewer():
                self.sprite_viewer = None

            def set_sprite(sprite: int):
                sprites = self.frame
                sprites[self.sprite_viewer_index] = sprite * 2
                self.frame = sprites

            self.sprite_viewer.destroyed.connect(remove_sprite_viewer)
            self.sprite_viewer.sprite_selected.connect(set_sprite)
            self.sprite_viewer.show()
        else:
            self.sprite_viewer.graphics_set = self.sprite_groups[widget_index].graphics_set
            self.sprite_viewer.palette_index = get_animations_palette_index(self.model.is_mario, widget_index)


class PlayerFrameEditorView(QWidget):
    clicked: SignalInstance = Signal(int, int)  # type: ignore

    def __init__(
        self,
        parent: Optional[QWidget],
        sprite_groups: list[SpriteGroupProtocol],
        zoom: int = 2,
    ):
        super().__init__(parent)

        self.sprite_groups = sprite_groups
        self._zoom = zoom

        self.layout_ = QHBoxLayout(self)
        self.widgets: list[SpriteViewerWidget] = []

        for idx, sprite_group in enumerate(sprite_groups):
            widget = SpriteViewerWidget(self, sprite_group, zoom=self.zoom)
            widget.clicked.connect(lambda x, y, idx=idx: self.clicked.emit(x + y * ANIMATION_WIDTH, idx))
            self.widgets.append(widget)
            self.layout_.addWidget(widget)

        self.setLayout(self.layout_)

    @property
    def zoom(self) -> int:
        return self._zoom

    @zoom.setter
    def zoom(self, value: int):
        self._zoom = value
        for widget in self.widgets:
            widget.zoom = value

    def _update(self):
        for (widget, sprite_group) in zip(self.widgets, self.sprite_groups):
            widget.sprite_group = sprite_group
            widget.update()
