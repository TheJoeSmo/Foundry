from typing import Optional

from attr import attrs
from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtGui import QCloseEvent, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QLayout,
    QStatusBar,
    QToolBar,
    QWidget,
)

from foundry import icon
from foundry.core.palette.Palette import MutablePalette, MutablePaletteProtocol
from foundry.core.palette.PaletteGroup import (
    MutablePaletteGroup,
    MutablePaletteGroupProtocol,
)
from foundry.core.player_animations import ANIMATION_WIDTH
from foundry.core.player_animations.PlayerAnimation import PlayerAnimation
from foundry.core.player_animations.util import (
    get_animations_palette_index,
    load_animations,
    load_player_animation_data,
    load_player_animations,
    load_power_up_offsets,
    load_power_up_palettes,
    save_player_animations_to_rom,
)
from foundry.core.point.Point import MutablePoint
from foundry.core.sprites import SPRITE_SIZE
from foundry.core.sprites.Sprite import Sprite, SpriteProtocol
from foundry.core.sprites.SpriteGroup import SpriteGroup, SpriteGroupProtocol
from foundry.core.UndoController import UndoController
from foundry.gui.CustomChildWindow import CustomChildWindow
from foundry.gui.PaletteEditorWidget import PaletteEditorWidget
from foundry.gui.PlayerFrameEditor import (
    PlayerFrameEditorController as PlayerFrameEditor,
)
from foundry.gui.SettingsDialog import SettingsDialog
from foundry.gui.Spinner import Spinner
from foundry.gui.SpriteViewerWidget import SpriteViewerWidget

POWERUPS = [
    ("Small Mario", 32, 53),
    ("Big Mario", 6, 48),
    ("Fire Mario", 16, 53),
    ("Raccoon Mario", 57, 53),
    ("Frog Mario", 56, 53),
    ("Tanooki Mario", 54, 53),
    ("Hammer Mario", 58, 53),
]


@attrs(slots=True, auto_attribs=True)
class PlayerViewerModel:
    is_mario: bool
    power_up: int
    power_up_offsets: list[int]
    palette_group: MutablePaletteGroupProtocol
    animations: list[PlayerAnimation]

    @classmethod
    def from_rom(
        cls,
        is_mario: bool = True,
        power_up: int = 0,
        power_up_offsets: Optional[list[int]] = None,
        palette_group: Optional[MutablePaletteGroupProtocol] = None,
        animations: Optional[list[PlayerAnimation]] = None,
    ):
        return cls(
            is_mario,
            power_up,
            power_up_offsets or load_power_up_offsets(),
            palette_group or load_power_up_palettes(),
            animations or load_player_animations(),
        )

    @classmethod
    def from_bytes(
        cls,
        is_mario: bool,
        power_up: int,
        power_up_offsets: bytes,
        palette_group: bytes,
        animations: bytes,
        page_offsets: bytes,
    ):
        return cls(
            is_mario,
            power_up,
            [i for i in power_up_offsets],
            MutablePaletteGroup(
                [MutablePalette([j for j in palette_group[i : (i + 4)]]) for i in range(len(palette_group) // 4)]
            ),
            load_animations(animations, page_offsets),
        )

    def to_bytes(self) -> tuple[bytes, bytes, bytes, bytes]:
        animation_bytes = bytearray()
        page_offset_bytes = bytearray()
        for animation in self.animations:
            ani_bytes, page_bytes = animation.to_bytes()
            ani_bytes = bytearray([i + 1 for i in ani_bytes])
            animation_bytes += ani_bytes
            page_offset_bytes += page_bytes

        return (
            bytes(o & 0xFF for o in self.power_up_offsets),
            bytes(self.palette_group),
            bytes(animation_bytes),
            bytes(page_offset_bytes),
        )


class PlayerViewerController(CustomChildWindow):
    power_up_changed: SignalInstance = Signal(int)  # type: ignore
    is_mario_changed: SignalInstance = Signal(bool)  # type: ignore
    palette_group_changed: SignalInstance = Signal(MutablePaletteGroupProtocol)  # type: ignore
    power_up_offsets_changed: SignalInstance = Signal(object)  # type: ignore
    destroyed: SignalInstance = Signal()  # type: ignore

    def __init__(
        self,
        parent: Optional[QWidget],
        title: str = "Player Viewer",
        is_mario: bool = True,
        power_up: int = 0,
        power_up_offsets: Optional[list[int]] = None,
        palette_group: Optional[MutablePaletteGroupProtocol] = None,
        animations: Optional[list[PlayerAnimation]] = None,
    ):
        super().__init__(parent, title)

        self.model = PlayerViewerModel.from_rom(is_mario, power_up, power_up_offsets, palette_group, animations)
        self.view = PlayerViewerView(self, self.sprite_groups)
        self.undo_controller = UndoController(self.model.to_bytes())
        self.frame_editor: Optional[PlayerFrameEditor] = None
        self.frame_editor_index = 0
        self.setCentralWidget(self.view)
        self.toolbar = QToolBar(self)
        self.side_toolbar = QToolBar(self)

        self.toolbar.setMovable(False)
        self.side_toolbar.setMovable(False)

        self.view.mouse_moved_over_widget.connect(self._on_mouse_move)
        self.view.clicked.connect(self._show_player_frame_editor)

        self.undo_action = self.toolbar.addAction(icon("rotate-ccw.svg"), "Undo Action")
        self.redo_action = self.toolbar.addAction(icon("rotate-cw.svg"), "Redo Action")
        self.zoom_out_action = self.toolbar.addAction(icon("zoom-out.svg"), "Zoom Out")
        self.zoom_in_action = self.toolbar.addAction(icon("zoom-in.svg"), "Zoom In")

        self.powerup_combo_box = QComboBox()
        for (name, x, y) in POWERUPS:
            powerup_icon = SettingsDialog._load_from_png(x, y)
            self.powerup_combo_box.addItem(powerup_icon, name)
        self.is_mario_check_box = QCheckBox()
        self.palette_editor = PaletteEditorWidget(self, self.palette)
        self.power_up_offset_spinner = Spinner(self, 0xFF)

        def change_zoom(offset: int):
            self.view.zoom += offset

        def undo(*_):
            self.model = PlayerViewerModel.from_bytes(self.is_mario, self.power_up, *self.undo_controller.undo())
            self._update()

        def redo(*_):
            self.model = PlayerViewerModel.from_bytes(self.is_mario, self.power_up, *self.undo_controller.redo())
            self._update()

        def set_power_up(value: int):
            self.power_up = value

        def set_is_mario(value: bool):
            self.is_mario = value

        def set_palette(value: MutablePaletteProtocol):
            self.palette = value

        def set_power_up_offset(value: int):
            self.power_up_offset = value

        self.undo_action.triggered.connect(undo)  # type: ignore
        self.undo_action.setEnabled(False)
        self.redo_action.triggered.connect(redo)  # type: ignore
        self.redo_action.setEnabled(False)
        self.zoom_out_action.triggered.connect(lambda *_: change_zoom(-1))  # type: ignore
        self.zoom_in_action.triggered.connect(lambda *_: change_zoom(1))  # type: ignore

        self.powerup_combo_box.currentIndexChanged.connect(set_power_up)  # type: ignore
        self.powerup_combo_box.setCurrentIndex(power_up)

        self.is_mario_check_box.setChecked(is_mario)
        self.is_mario_check_box.toggled.connect(set_is_mario)  # type: ignore

        self.palette_editor.palette_changed.connect(set_palette)

        self.power_up_offset_spinner.valueChanged.connect(set_power_up_offset)  # type: ignore

        side_toolbar_layout = QFormLayout(self)
        side_toolbar_layout.addRow("Power Up", self.powerup_combo_box)
        side_toolbar_layout.addRow("Mario or Luigi", self.is_mario_check_box)
        side_toolbar_layout.addRow("palette Editor", self.palette_editor)
        side_toolbar_layout.addRow("Page Offset", self.power_up_offset_spinner)

        class LayoutWidget(QWidget):
            def __init__(self, parent, layout: QLayout):
                super().__init__(parent)
                self.setLayout(layout)

        self.side_toolbar.addWidget(LayoutWidget(self.side_toolbar, side_toolbar_layout))

        self.addToolBar(self.toolbar)
        self.addToolBar(Qt.RightToolBarArea, self.side_toolbar)

        self.setStatusBar(QStatusBar(self))
        self.layout().setSizeConstraint(QLayout.SetFixedSize)

    def closeEvent(self, event: QCloseEvent):
        if self.frame_editor is not None:
            self.frame_editor.close()
        self.destroyed.emit()
        super().closeEvent(event)

    @property
    def power_up(self) -> int:
        return self.model.power_up

    @power_up.setter
    def power_up(self, power_up: int):
        self.model.power_up = power_up
        self._update_palette_editor()
        self._update_view_animations()
        self.power_up_offset_spinner.setValue(self.power_up_offset)
        self.powerup_combo_box.setCurrentIndex(power_up)
        self.power_up_changed.emit(power_up)

    @property
    def is_mario(self) -> bool:
        return self.model.is_mario

    @is_mario.setter
    def is_mario(self, is_mario: bool):
        self.model.is_mario = is_mario
        self._update()
        self.is_mario_check_box.setChecked(is_mario)
        self.is_mario_changed.emit(is_mario)

    @property
    def power_up_offset(self) -> int:
        return self.power_up_offsets[self.power_up]

    @power_up_offset.setter
    def power_up_offset(self, offset: int):
        offsets = self.power_up_offsets
        offsets[self.power_up] = offset
        self.power_up_offsets = offsets

    @property
    def power_up_offsets(self) -> list[int]:
        return self.model.power_up_offsets

    @power_up_offsets.setter
    def power_up_offsets(self, offsets: list[int]):
        self.model.power_up_offsets = offsets
        self.undo_controller.do(self.model.to_bytes())
        self.update()
        self.power_up_offsets_changed.emit(offsets)

    @property
    def palette(self) -> MutablePaletteProtocol:
        return self.palette_group[get_animations_palette_index(self.is_mario, self.power_up)]

    @palette.setter
    def palette(self, palette: MutablePaletteProtocol):
        palette_group = self.palette_group
        palette_group[get_animations_palette_index(self.is_mario, self.power_up)] = palette
        self.palette_group = palette_group

    @property
    def palette_group(self) -> MutablePaletteGroupProtocol:
        return self.model.palette_group

    @palette_group.setter
    def palette_group(self, palette_group: MutablePaletteGroupProtocol):
        self.model.palette_group = palette_group
        self.undo_controller.do(self.model.to_bytes())
        self._update()
        self.palette_group_changed.emit(palette_group)

    @property
    def sprite_groups(self) -> list[SpriteGroupProtocol]:
        sprite_groups: list[SpriteGroupProtocol] = []

        for animation in load_player_animation_data(
            self.model.animations,
            self.model.palette_group,
            self.model.is_mario,
            self.model.power_up,
            self.model.power_up_offsets,
        ):
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

    def _update(self):
        self.undo_action.setEnabled(self.undo_controller.can_undo)
        self.redo_action.setEnabled(self.undo_controller.can_redo)
        save_player_animations_to_rom(*self.model.to_bytes())
        self._update_palette_editor()
        self._update_view_animations()
        if self.frame_editor is not None:
            self.frame_editor.is_mario = self.is_mario

    def _update_palette_editor(self):
        self.palette_editor._palette = self.palette
        self.palette_editor._update()

    def _update_view_animations(self):
        self.view.sprite_groups = self.sprite_groups
        self.view._update()

    def _show_player_frame_editor(self, index: int):
        self.frame_editor_index = index

        if self.frame_editor is None:
            self.frame_editor = PlayerFrameEditor(
                self, self.model.animations[index], self.power_up_offsets, self.palette_group, self.is_mario
            )

            def remove_frame_editor():
                self.frame_editor = None

            def change_frame_offset(offset: int):
                self.model.animations[self.frame_editor_index].offset = offset
                self.undo_controller.do(self.model.to_bytes())
                self._update()

            def change_frame_sprites(sprites: bytearray):
                self.model.animations[self.frame_editor_index].animations = sprites
                self.undo_controller.do(self.model.to_bytes())
                self._update()

            self.frame_editor.destroyed.connect(remove_frame_editor)
            self.frame_editor.offset_changed.connect(change_frame_offset)
            self.frame_editor.frames_changed.connect(change_frame_sprites)
            self.frame_editor.show()
        else:
            self.frame_editor.model.animation = self.model.animations[index]
            self.frame_editor._update_view_animations()

    def _on_mouse_move(self, x: int, y: int, index: int, hex_index: str):
        self.statusBar().showMessage(f"Row: {y}, Column: {x}, Index: {index} / {hex_index}")


class PlayerViewerView(QWidget):
    mouse_moved_over_widget: SignalInstance = Signal(int, int, int, str)  # type: ignore
    clicked: SignalInstance = Signal(int)  # type: ignore

    ANIMATIONS_PER_ROW = 9
    ANIMATIONS_PER_COLUMN = 9

    def __init__(
        self,
        parent: Optional[QWidget],
        sprite_groups: list[SpriteGroupProtocol],
        zoom: int = 2,
    ):
        super().__init__(parent)

        self.sprite_groups = sprite_groups
        self._zoom = zoom

        self.layout_ = QGridLayout(self)
        self.widgets: list[SpriteViewerWidget] = []

        for idx, sprite_group in enumerate(sprite_groups):
            widget = SpriteViewerWidget(self, sprite_group, zoom=self.zoom)
            widget.mouse_moved_over_widget.connect(
                lambda *_, idx=idx: self.mouse_moved_over_widget.emit(
                    idx % self.ANIMATIONS_PER_ROW,
                    idx // self.ANIMATIONS_PER_ROW,
                    idx,
                    hex(idx).upper().replace("X", "x"),
                )
            )
            widget.clicked.connect(lambda *_, idx=idx: self.clicked.emit(idx))
            self.widgets.append(widget)
            self.layout_.addWidget(widget, idx // self.ANIMATIONS_PER_ROW, idx % self.ANIMATIONS_PER_ROW)

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
