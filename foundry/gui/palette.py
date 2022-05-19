from typing import Optional

from attr import attrs
from PySide6.QtCore import QSize, Signal, SignalInstance
from PySide6.QtGui import QColor, QMouseEvent, QPixmap, Qt
from PySide6.QtWidgets import (
    QAbstractButton,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from foundry.core.palette import (
    COLORS_PER_PALETTE,
    PALETTE_GROUPS_PER_OBJECT_SET,
    PALETTES_PER_PALETTES_GROUP,
    ColorPalette,
    Palette,
    PaletteGroup,
    get_internal_palette_offset,
)
from foundry.game.File import ROM
from foundry.game.level.Level import Level
from foundry.game.level.LevelRef import LevelRef
from foundry.gui.CustomDialog import CustomDialog


class ColorButtonWidget(QLabel):
    """
    A colored button that can be pressed and interacted with

    Attributes
    ----------
    clicked: Signal
        Slot associated with the button being clicked.
    size_changed: Signal[QSize]
        Slot associated with the button changing size.
    color_changed: Signal[QColor]
        Slot associated with the button changing color.
    selected_changed: Signal[bool]
        Slot associated with the button changing its selected state.
    """

    clicked: SignalInstance = Signal()  # type: ignore
    size_changed: SignalInstance = Signal(QSize)  # type: ignore
    color_changed: SignalInstance = Signal(QColor)  # type: ignore
    selected_changed: SignalInstance = Signal(bool)  # type: ignore

    def __init__(
        self,
        parent: Optional[QWidget],
        color: Optional[QColor] = None,
        size: Optional[QSize] = None,
        selected: bool = False,
    ):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        if color is not None:
            self._color = color
        else:
            self._color = QColor(Qt.white)
        if size is not None:
            self._size_ = size
        else:
            self._size_ = QSize(16, 16)
        self._selected = selected
        self._update()

    @property
    def size_(self) -> QSize:
        return self._size_

    @size_.setter
    def size_(self, size: QSize):
        self._size_ = size
        self.size_changed.emit(size)
        self._update()

    @property
    def color(self) -> QColor:
        return self._color

    @color.setter
    def color(self, color: QColor):
        self._color = color
        self.color_changed.emit(color)
        self._update()

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, selected: bool):
        self._selected = selected
        self.selected_changed.emit(selected)
        self._update()

    def _update(self):
        pix = QPixmap(self.size_)
        pix.fill(self.color)
        self.setPixmap(pix)

        if self.selected:
            if self.color.lightnessF() < 0.25:
                self.setStyleSheet("border-color: rgb(255, 255, 255); border-width: 2px; border-style: solid")
            else:
                self.setStyleSheet("border-color: rgb(0, 0, 0); border-width: 2px; border-style: solid")
        else:
            rgb = self.color.getRgb()
            self.setStyleSheet(
                f"border-color: rgb({rgb[0]}, {rgb[1]}, {rgb[2]}); border-width: 2px; border-style: solid"
            )

        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.clicked.emit()


class ColorSelector(CustomDialog):
    ROWS = 4
    COLUMNS = 16

    ok_clicked: SignalInstance = Signal(int)  # type: ignore

    def __init__(
        self,
        parent: Optional[QWidget],
        title: str = "NES Color Table",
        size: Optional[QSize] = None,
        color_palette: Optional[ColorPalette] = None,
    ):
        super().__init__(parent, title=title)

        self.size_ = size if not None else QSize(24, 24)
        self.color_palette = color_palette if color_palette is not None else ColorPalette.as_default()

        self._selected_button = 0

        self.layout_ = QGridLayout()
        self.layout_.setSpacing(0)

        self._color_buttons = []
        for row in range(self.ROWS):
            for column in range(self.COLUMNS):
                color = self.color_palette.colors[row * self.COLUMNS + column]
                button = ColorButtonWidget(self, color.qcolor, self.size_)
                button.setLineWidth(0)
                self._color_buttons.append(button)
                self.layout_.addWidget(button, row, column)
        self._color_buttons[0].selected = True

        for idx, btn in enumerate(self._color_buttons):
            btn.clicked.connect(lambda idx=idx: self._on_click(idx))

        self.buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttons.clicked.connect(self._on_button)  # type: ignore

        layout = QVBoxLayout(self)
        layout.addLayout(self.layout_)

        layout.addWidget(self.buttons, alignment=Qt.AlignCenter)

    @property
    def last_selected_color_index(self) -> int:
        return self._selected_button

    def _on_click(self, index: int):
        self._color_buttons[self._selected_button].selected = False
        self._color_buttons[index].selected = True
        self._selected_button = index

    def _on_button(self, button: QAbstractButton):
        if button is self.buttons.button(QDialogButtonBox.Ok):  # ok button
            self.accept()
        else:
            self.reject()


class PaletteWidget(QWidget):
    """
    A widget to view the palette.

    Attributes
    ----------
    palette_changed: Signal[palette]
        Slot associated with the palette viewer changing its palette.
    """

    palette_changed: SignalInstance = Signal(Palette)  # type: ignore

    def __init__(self, parent: Optional[QWidget], palette: Palette):
        super().__init__(parent)
        self._palette = palette

        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 2, 0, 2)

        self._buttons = [ColorButtonWidget(self, color) for color in palette.colors]

        for button in self._buttons:
            layout.addWidget(button)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.parent}, {self.palette})"

    @property
    def palette(self) -> Palette:
        return self._palette

    @palette.setter
    def palette(self, palette: Palette):
        self._palette = palette
        self.palette_changed.emit(palette)
        self._update()

    def _update(self):
        for idx, color in enumerate(self.palette.colors):
            self._buttons[idx].color = color


class PaletteEditorWidget(PaletteWidget):
    def __init__(self, parent: Optional[QWidget], palette: Palette):
        super().__init__(parent, palette)

        for idx, btn in enumerate(self._buttons):
            btn.clicked.connect(lambda idx=idx: self._open_color_selector(idx))

    def _open_color_selector(self, button_index: int):
        selector = ColorSelector(self)

        if QDialog.Accepted == selector.exec_():
            palette = list(self.palette)
            palette[button_index] = selector.last_selected_color_index
            self.palette = Palette(tuple(palette))


@attrs(slots=True, auto_attribs=True)
class PaletteGroupModel:
    tileset: int
    background_index: int
    sprite_index: int
    background_palette_group: PaletteGroup
    sprite_palette_group: PaletteGroup
    changed: bool = False
    background_palette_group_backup: Optional[PaletteGroup] = None
    sprite_palette_group_backup: Optional[PaletteGroup] = None

    def restore(self):
        self.background_palette_group = (
            self.background_palette_group_backup
            if self.background_palette_group_backup is not None
            else PaletteGroup.from_tileset(self.tileset, self.background_index)
        )
        self.sprite_palette_group = (
            self.sprite_palette_group_backup
            if self.sprite_palette_group_backup is not None
            else PaletteGroup.from_tileset(self.tileset, self.sprite_index + PALETTE_GROUPS_PER_OBJECT_SET)
        )

    def soft_save(self):
        if self.background_palette_group_backup is None:
            self.background_palette_group_backup = PaletteGroup.from_tileset(self.tileset, self.background_index)
        if self.sprite_palette_group_backup is None:
            self.sprite_palette_group_backup = PaletteGroup.from_tileset(
                self.tileset, self.sprite_index + PALETTE_GROUPS_PER_OBJECT_SET
            )
        self._save()

    def save(self, rom: Optional[ROM] = None):
        self.background_palette_group_backup = None
        self.sprite_palette_group_backup = None
        self._save(rom)

    def _save(self, rom: Optional[ROM] = None):
        bg_offset = (
            get_internal_palette_offset(self.tileset)
            + self.background_index * PALETTES_PER_PALETTES_GROUP * COLORS_PER_PALETTE
        )
        spr_offset = (
            get_internal_palette_offset(self.tileset)
            + (self.sprite_index + PALETTE_GROUPS_PER_OBJECT_SET) * PALETTES_PER_PALETTES_GROUP * COLORS_PER_PALETTE
        )

        if rom is None:
            rom = ROM()
        rom.write(bg_offset, bytes(self.background_palette_group))
        rom.write(spr_offset, bytes(self.sprite_palette_group))


class PaletteGroupController(QWidget):
    palette_group_changed: SignalInstance = Signal(PaletteGroup, PaletteGroup)  # type: ignore

    def __init__(
        self,
        parent: Optional[QWidget],
        tileset: int = 0,
        bg_offset: int = 0,
        spr_offset: int = 0,
        bg_palette_group: PaletteGroup = PaletteGroup(),
        spr_palette_group: PaletteGroup = PaletteGroup(),
    ):
        super().__init__(parent)

        self.model = PaletteGroupModel(tileset, bg_offset, spr_offset, bg_palette_group, spr_palette_group)

        layout = QHBoxLayout()
        layout.setSpacing(0)

        self.bg_widget = PaletteGroupEditor(self, self.model.background_palette_group)
        self.spr_widget = PaletteGroupEditor(self, self.model.sprite_palette_group)

        layout.addWidget(self.bg_widget)
        layout.addWidget(self.spr_widget)

        self.bg_widget.palette_group_changed.connect(lambda *_: self.on_palette_update())
        self.spr_widget.palette_group_changed.connect(lambda *_: self.on_palette_update())

        self.setLayout(layout)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({self.parent}, {self.model.tileset}, "
            + f"{self.model.background_index}, {self.model.sprite_index}, "
            + f"{self.model.background_palette_group}, {self.model.sprite_palette_group})"
        )

    def load_from_level(self, level: Level):
        self.model.tileset = level.object_set_number
        self.model.background_index = level.object_palette_index
        self.model.sprite_index = level.enemy_palette_index
        self.model.restore()
        self._changed = False
        self.silent_update()

    def restore(self):
        self.model.restore()
        self.model.soft_save()
        self._changed = False
        self.silent_update()

    def save(self, rom: Optional[ROM] = None):
        self.model.save(rom)
        self._changed = False

    def silent_update(self):
        self.bg_widget._palette_group = self.model.background_palette_group
        self.bg_widget._update()
        self.spr_widget._palette_group = self.model.sprite_palette_group
        self.spr_widget._update()

    @property
    def changed(self) -> bool:
        return self.model.changed

    @changed.setter
    def changed(self, value: bool):
        self.model.changed = value

    def on_palette_update(self):
        self.model.background_palette_group = self.bg_widget.palette_group
        self.model.sprite_palette_group = self.spr_widget.palette_group
        self.changed = True
        self.model.soft_save()
        self.palette_group_changed.emit(self.model.background_palette_group, self.model.sprite_palette_group)


class PaletteGroupEditor(QWidget):
    palette_group_changed: SignalInstance = Signal(PaletteGroup)  # type: ignore

    def __init__(self, parent: Optional[QWidget], palette_group: PaletteGroup):
        super().__init__(parent)
        self._palette_group = palette_group

        layout = QVBoxLayout()
        layout.setSpacing(0)

        self._palettes: list[PaletteEditorWidget] = []
        for idx, palette in enumerate(palette_group.palettes):
            widget = PaletteEditorWidget(self, palette)
            widget.palette_changed.connect(lambda *_, idx=idx: self._on_palette_changed(idx))
            self._palettes.append(widget)
            layout.addWidget(widget)

        self.setLayout(layout)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.parent}, {self.palette_group})"

    @property
    def palette_group(self) -> PaletteGroup:
        return self._palette_group

    @palette_group.setter
    def palette_group(self, palette_group: PaletteGroup):
        self._palette_group = palette_group
        self.palette_group_changed.emit(palette_group)
        self._update()

    def _update(self):
        for idx, palette in enumerate(self._palettes):
            palette._palette = self._palette_group[idx]
            palette._update()

    def _on_palette_changed(self, palette_index: int):
        palette_group = list(self.palette_group)
        palette_group[palette_index] = self._palettes[palette_index].palette
        for index, palette in enumerate(palette_group):
            pal = list(palette)
            pal[0] = palette_group[palette_index][0]
            palette_group[index] = Palette(tuple(pal))
        self.palette_group = PaletteGroup(tuple(palette_group))


class PaletteViewer(CustomDialog):
    palettes_per_row = 4

    def __init__(self, parent, level_ref: LevelRef):
        title = f"Palette Groups for Object Set {level_ref.level.object_set_number}"

        super(PaletteViewer, self).__init__(parent, title=title)

        self.level_ref = level_ref

        layout = QGridLayout(self)

        for palette_group in range(PALETTE_GROUPS_PER_OBJECT_SET):
            group_box = QGroupBox()
            group_box.setTitle(f"Palette Group {palette_group}")

            group_box_layout = QVBoxLayout(group_box)
            group_box_layout.setSpacing(0)

            pal = PaletteGroup.from_tileset(self.level_ref.level.object_set_number, palette_group)

            for idx in range(PALETTES_PER_PALETTES_GROUP):
                group_box_layout.addWidget(PaletteWidget(self, pal[idx]))

            row = palette_group // self.palettes_per_row
            col = palette_group % self.palettes_per_row

            layout.addWidget(group_box, row, col)
