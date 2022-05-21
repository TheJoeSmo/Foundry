from __future__ import annotations

from typing import Optional

from attr import attrs, evolve, field
from attr.validators import instance_of
from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtGui import QMouseEvent, QPixmap, Qt
from PySide6.QtWidgets import (
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

from foundry.core.geometry import Size
from foundry.core.palette import (
    COLORS_PER_PALETTE,
    PALETTE_GROUPS_PER_OBJECT_SET,
    PALETTES_PER_PALETTES_GROUP,
    Color,
    ColorPalette,
    Palette,
    PaletteGroup,
    get_internal_palette_offset,
)
from foundry.core.UndoController import UndoController
from foundry.game.File import ROM
from foundry.game.level.Level import Level
from foundry.game.level.LevelRef import LevelRef
from foundry.gui.CustomDialog import CustomDialog


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class ColorButtonState:
    """
    The model of a colored button.

    Attributes
    ----------
    color: Color
        The color of the button, by default the first color of the NES palette.
    size: Size
        The fixed size of the button, by default (16, 16).
    selected: bool
        If the button is selected, by default unselected.
    """

    color: Color = field(validator=[instance_of(Color)], default=ColorPalette.as_default().default_color)
    size: Size = field(validator=[instance_of(Size)], default=Size(16, 16))
    selected: bool = field(validator=[instance_of(bool)], default=False)


class ColorButtonWidget(QLabel):
    """
    A colored button that can be pressed and interacted with

    Signals
    -------
    clicked: SignalInstance
        Slot associated with the button being clicked.
    size_changed: SignalInstance
        Slot associated with the button changing size.
    color_changed: SignalInstance
        Slot associated with the button changing color.
    selected_changed: SignalInstance
        Slot associated with the button changing its selected state.

    Attributes
    ----------
    parent: None | QWidget
        The parent of this widget if one exists.
    color: Color
        The color of the button, by default the first color of the NES palette.
    size_: Size
        The size of the button, by default (16, 16).
    selected: bool
        If the button is selected, by default unselected.
    undo_controller: UndoController[ColorButtonState]
        The controller in charge of handling undo and redo actions, a new one is generated if None is provided.
    """

    clicked: SignalInstance = Signal()  # type: ignore
    size_changed: SignalInstance = Signal(Size)  # type: ignore
    color_changed: SignalInstance = Signal(Color)  # type: ignore
    selected_changed: SignalInstance = Signal(bool)  # type: ignore

    def __init__(
        self,
        parent: None | QWidget,
        color: Color = ColorPalette.as_default().default_color,
        size_: Size = Size(16, 16),
        selected: bool = False,
        undo_controller: None | UndoController[ColorButtonState] = None,
    ):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._state = ColorButtonState(color, size_, selected)
        self.undo_controller = undo_controller or UndoController(self.state)
        self._update()

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, type(self))
            and self._state == other.state
            and self.undo_controller == other.undo_controller
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}({self.parent}, {self.color}, {self.size_}, "
            + f"{self.selected}, {self.undo_controller})"
        )

    @property
    def size_(self) -> Size:
        """
        Provides the size of the button to be displayed.

        Returns
        -------
        Size
            The size of the button.
        """
        return self._state.size

    @size_.setter
    def size_(self, size: Size):
        if size != self._state.size:
            self.do(evolve(self.state, size=size))

    @property
    def color(self) -> Color:
        """
        Provides the color of the button to be displayed.

        Returns
        -------
        Color
            The color of the button.
        """
        return self._state.color

    @color.setter
    def color(self, color: Color):
        if color != self._state.color:
            self.do(evolve(self.state, color=color))

    @property
    def selected(self) -> bool:
        """
        If the button is considered selected.

        Returns
        -------
        bool
            If the button is currently selected.
        """
        return self._state.selected

    @selected.setter
    def selected(self, selected: bool):
        if selected != self._state.selected:
            self.do(evolve(self.state, selected=selected))

    @property
    def state(self) -> ColorButtonState:
        """
        Provides the current state of the instance.

        Returns
        -------
        ColorButtonState
            A tuple of the color, size, and if the button is selected of this instance.
        """
        return self._state

    @state.setter
    def state(self, state: ColorButtonState):
        if self.state != state:
            self.do(state)

    def do(self, new_state: ColorButtonState) -> ColorButtonState:
        """
        Does an action through the controller, adding it to the undo stack and clearing the redo
        stack, respectively.

        Parameters
        ----------
        new_state : ColorButtonState
            The new state to be stored.

        Returns
        -------
        ColorButtonState
            The new state that has been stored.
        """
        self._update_state(new_state)
        return self.undo_controller.do(new_state)

    @property
    def can_undo(self) -> bool:
        """
        Determines if there is any states inside the undo stack.

        Returns
        -------
        bool
            If there is an undo state available.
        """
        return self.undo_controller.can_undo

    def undo(self) -> ColorButtonState:
        """
        Undoes the last state, bring the previous.

        Returns
        -------
        ColorButtonState
            The new state that has been stored.
        """
        self._update_state(self.undo_controller.undo())
        return self.state

    @property
    def can_redo(self) -> bool:
        """
        Determines if there is any states inside the redo stack.

        Returns
        -------
        bool
            If there is an redo state available.
        """
        return self.undo_controller.can_redo

    def redo(self) -> ColorButtonState:
        """
        Redoes the previously undone state.

        Returns
        -------
        ColorButtonState
            The new state that has been stored.
        """
        self._update_state(self.undo_controller.redo())
        return self.state

    def _update_state(self, state: ColorButtonState):
        """
        Handles all updating of the state, sending any signals and updates to the display if needed.

        Parameters
        ----------
        state : ColorButtonState
            The new state of the editor.
        """
        if self._state.color != state.color:
            self.color_changed.emit(state.color)
            self._state = evolve(self.state, color=state.color)

        if self._state.size != state.size:
            self.size_changed.emit(state.size)
            self._state = evolve(self.state, size=state.size)

        if self._state.selected != state.selected:
            self.selected_changed.emit(state.selected)
            self._state = evolve(self.state, selected=state.selected)

        self._update()

    def _update(self):
        pix = QPixmap(self.state.size.qsize)
        pix.fill(self.color.qcolor)
        self.setPixmap(pix)

        if self.selected:
            if self.color.qcolor.lightnessF() < 0.25:
                self.setStyleSheet("border-color: rgb(255, 255, 255); border-width: 2px; border-style: solid")
            else:
                self.setStyleSheet("border-color: rgb(0, 0, 0); border-width: 2px; border-style: solid")
        else:
            self.setStyleSheet(
                f"border-color: rgb({self.color.red}, {self.color.green}, {self.color.blue});"
                + "border-width: 2px; border-style: solid"
            )

        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.clicked.emit()


@attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
class ColorSelectorState:
    """
    The model of a color selector.

    Attributes
    ----------
    title: str
        The title of the dialog, by default "NES Color Table".
    size: Size
        The size of the color buttons, by default (24, 24).
    color_palette: ColorPalette
        The palette of color options to select from, by default the NES palette.
    selected_button: int
        The currently selected colored button, by default 0.
    rows: int = 4
        The number of rows to display.
    columns: int = 16
        The number of columns to display.
    """

    title: str = "NES Color Table"
    size: Size = Size(24, 24)
    color_palette: ColorPalette = ColorPalette.as_default()
    selected_button: int = 0
    rows: int = 4
    columns: int = 16


class ColorSelector(CustomDialog):
    """
    A widget in charge of selecting a color from a color palette.

    Signals
    -------
    ok_clicked: SignalInstance
        The index of the last color button selected after the user pressed ok.
    """

    ok_clicked: SignalInstance = Signal(int)  # type: ignore

    def __init__(
        self,
        parent: None | QWidget,
        title: str = "NES Color Table",
        size: Size = Size(24, 24),
        color_palette: ColorPalette = ColorPalette.as_default(),
        selected_button: int = 0,
        rows: int = 4,
        columns: int = 16,
    ):
        super().__init__(parent, title=title)

        self._state = ColorSelectorState(title, size, color_palette, selected_button, rows, columns)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(0)

        self._buttons = [ColorButtonWidget(self, color, self._state.size) for color in self._state.color_palette.colors]
        for index, button in enumerate(self._buttons):
            button.setLineWidth(0)
            button.clicked.connect(lambda index=index: self._on_click(index))
            grid_layout.addWidget(button, index // self._state.columns, index % self._state.columns)
        self._buttons[self._state.selected_button].selected = True

        self._dialog = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)  # type: ignore
        self._dialog.clicked.connect(self._on_dialog)  # type: ignore

        layout = QVBoxLayout(self)
        layout.addLayout(grid_layout)
        layout.addWidget(self._dialog, alignment=Qt.AlignCenter)  # type: ignore

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}({self.parent}, {self._state.title}, {self._state.size}, "
            + f"{self._state.color_palette}, {self._state.selected_button}, {self._state.rows}, "
            + f"{self._state.columns})"
        )

    @property
    def last_selected_color_index(self) -> int:
        """
        Provides the index of the last selected colored button.

        Returns
        -------
        int
            The index of the last selected button.
        """
        return self._state.selected_button

    def _on_click(self, index: int):
        self._buttons[self._state.selected_button].selected = False
        self._buttons[index].selected = True
        self._state = evolve(self._state, selected_button=index)

    def _on_dialog(self, button):
        if button is self._dialog.button(QDialogButtonBox.Ok):
            self.ok_clicked.emit(self.last_selected_color_index)
            self.accept()
        else:
            self.reject()


class PaletteWidget(QWidget):
    """
    A widget to view a palette.

    Signals
    -------
    palette_changed: SignalInstance
        A signal which is activated when the palette changes.

    Attributes
    ----------
    palette: Palette
        The palette being displayed by the widget.
    undo_controller: UndoController[Palette]
        The undo controller, which is responsible for undoing and redoing any action.
    """

    palette_changed: SignalInstance = Signal(Palette)  # type: ignore

    def __init__(
        self, parent: Optional[QWidget], palette: Palette, undo_controller: None | UndoController[Palette] = None
    ):
        super().__init__(parent)

        self._palette = palette
        self.undo_controller = undo_controller or UndoController(palette)
        self._display = PaletteDisplay(self, palette)

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, type(self))
            and self._palette == other.palette
            and self.undo_controller == other.undo_controller
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.parent}, {self.palette})"

    @property
    def palette(self) -> Palette:
        """
        The current palette being displayed by the widget.

        Returns
        -------
        Palette
            The palette being displayed by the widget.
        """
        return self._palette

    @palette.setter
    def palette(self, palette: Palette):
        self.do(palette)
        self.palette_changed.emit(palette)

    def do(self, palette: Palette) -> Palette:
        """
        Does an action through the controller, adding it to the undo stack and clearing the redo
        stack, respectively.

        Parameters
        ----------
        palette : Palette
            The new palette to be stored.

        Returns
        -------
        Palette
            The new state that has been stored.
        """
        self._update_palette(palette)
        return self.undo_controller.do(palette)

    @property
    def can_undo(self) -> bool:
        """
        Determines if there is any palettes inside the undo stack.

        Returns
        -------
        bool
            If there is an undo palette available.
        """
        return self.undo_controller.can_undo

    def undo(self) -> Palette:
        """
        Undoes the last palette, bring the previous.

        Returns
        -------
        Palette
            The new palette that has been stored.
        """
        self._update_palette(self.undo_controller.undo())
        return self.palette

    @property
    def can_redo(self) -> bool:
        """
        Determines if there is any palettes inside the redo stack.

        Returns
        -------
        bool
            If there is an redo palette available.
        """
        return self.undo_controller.can_redo

    def redo(self) -> Palette:
        """
        Redoes the previously undone palette.

        Returns
        -------
        Palette
            The new state that has been stored.
        """
        self._update_palette(self.undo_controller.redo())
        return self.palette

    def _update_palette(self, palette: Palette):
        """
        Handles all updating of the palette, sending any signals and updates to the display if needed.

        Parameters
        ----------
        palette : Palette
            The new palette of the editor.
        """
        if self._palette != palette or self.undo_controller.state != palette:
            self.palette_changed.emit(palette)
            self._palette = palette
            self._display.palette = palette


class PaletteEditorWidget(PaletteWidget):
    def __init__(
        self, parent: Optional[QWidget], palette: Palette, undo_controller: None | UndoController[Palette] = None
    ):
        super().__init__(parent, palette, undo_controller)

        self._display.button_clicked.connect(self._open_color_selector)

    # Separated to help monkey-patch for testing
    def _generate_color_selector(self) -> ColorSelector:
        return ColorSelector(self)

    def _open_color_selector(self, button_index: int):
        selector = self._generate_color_selector()

        if QDialog.Accepted == selector.exec_():
            palette = list(self.palette)
            palette[button_index] = selector.last_selected_color_index
            self.palette = Palette(tuple(palette))


class PaletteDisplay(QHBoxLayout):
    """
    The display of a palette, containing each of the respective colors.

    Attributes
    ----------
    buttons: list[ColorButtonWidget]
        A list containing each of the colors of the palette provided.
    """

    button_clicked: SignalInstance = Signal(int)  # type: ignore

    buttons: list[ColorButtonWidget]

    def __init__(self, parent: QWidget, palette: Palette):
        super().__init__(parent)
        self.setContentsMargins(1, 2, 0, 2)
        self.parent_ = parent
        self.palette = palette

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.parent_}, {self.palette})"

    @property
    def palette(self) -> Palette:
        """
        The palette that is being represented by the display.

        Returns
        -------
        Palette
            The palette that is being represented by `buttons` of this display.
        """
        return Palette(
            tuple(self._color_palette.colors.index(button.color) for button in self.buttons), self._color_palette
        )

    @palette.setter
    def palette(self, palette: Palette):
        self._clear()
        self._color_palette = palette.color_palette
        self.buttons = [ColorButtonWidget(self.parent_, color) for color in palette.colors]
        for index, button in enumerate(self.buttons):
            button.clicked.connect(lambda index=index, *_: self.button_clicked.emit(index))
            self.addWidget(button)

    def _clear(self):
        """
        Clears the display so new buttons can be placed inside of it.
        """
        while self.count():
            child = self.takeAt(0)
            if widget := child.widget():
                widget.deleteLater()


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
