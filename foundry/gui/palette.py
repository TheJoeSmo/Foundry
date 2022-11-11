from collections.abc import Sequence
from typing import ClassVar

from attr import attrs
from PySide6.QtGui import QPixmap, Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QSizePolicy, QVBoxLayout

from foundry.core.geometry import Size
from foundry.core.gui import (
    BaseModel,
    Click,
    DialogControl,
    Key,
    KeySequence,
    Modifier,
    MouseWheelEvent,
    Orientation,
    Selection,
    SignalInstance,
    UndoRedoExtendedForwarder,
)
from foundry.core.palette import Color, ColorPalette, Palette, PaletteGroup
from foundry.gui.core import (
    Dialog,
    DialogEvent,
    DialogOption,
    KeyHandler,
    Label,
    MouseAggregator,
    MouseEvent,
    MouseEventAggregate,
    MouseHandler,
    TabBar,
    Widget,
    generate_border,
)


class ColorButton(Label, MouseHandler):
    color: Color
    button_size: Size
    selection_type: Selection

    @attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
    class Model(BaseModel):
        color: Color = Color(0, 0, 0)
        button_size: Size = Size(16, 16)
        selection_type: Selection = Selection.NONE

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.color}, {self.button_size}, {self.selection_type})"

    def __str__(self) -> str:
        if self.selection_type is not Selection.NONE:
            return f"{self.__class__.__name__}({self.color}, {self.selection_type})"
        return f"{self.__class__.__name__}({self.color})"

    def initialize_state(self, model: Model, *args, **kwargs) -> None:
        super().initialize_state(model, *args, **kwargs)

        self.setFixedSize(model.button_size.width, model.button_size.height)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.change_state(model)

    def change_state(self, model: Model) -> None:
        pix: QPixmap = QPixmap(model.button_size.to_qt())
        pix.fill(model.color.to_qt())
        self.setPixmap(pix)

        r, g, b = model.color.red, model.color.green, model.color.blue
        if model.selection_type is Selection.NONE:
            self.setStyleSheet(f"border-color: rgb({r}, {g}, {b}); " f"border-width: 2px; border-style: solid")
        elif model.selection_type is Selection.UNDO or model.selection_type is Selection.REDO:
            if model.color.to_qt().lightnessF() < 0.25:
                self.setStyleSheet(
                    f"border-color: qlineargradient("
                    f"spread:pad, x1:0 y1:0, x2:1 y2:0, "
                    f"stop:0 rgba({min(255, r + 120)}, {min(255, g + 120)}, {min(255, b + 120)}, 255), "
                    f"stop:0.25 rgba({r}, {g}, {b}, 255), "
                    f"stop:0.5 rgba({r}, {g}, {b}, 255), "
                    f"stop:0.75 rgba({min(255, r + 120)}, {min(255, g + 120)}, {min(255, b + 120)}, 255));"
                    f"border-width: 2px; border-style: solid;"
                )
            else:
                self.setStyleSheet(
                    f"border-color: qlineargradient("
                    f"spread:pad, x1:0 y1:0, x2:1 y2:0, "
                    f"stop:0 rgba({max(0, r - 75)}, {max(0, g - 75)}, {max(0, b - 75)}, 255), "
                    f"stop:0.25 rgba({r}, {g}, {b}, 255), "
                    f"stop:0.5 rgba({r}, {g}, {b}, 255), "
                    f"stop:0.75 rgba({max(0, r - 75)}, {max(0, g - 75)}, {max(0, b - 75)}, 255)); "
                    f"border-width: 2px; border-style: solid;"
                )
        elif model.selection_type is Selection.SECONDARY:
            if model.color.to_qt().lightnessF() < 0.25:
                self.setStyleSheet(
                    f"border-color: qlineargradient("
                    f"spread:pad, x1:0 y1:0, x2:1 y2:0, "
                    f"stop:0 rgba({min(255, r + 120)}, {min(255, g + 120)}, {min(255, b + 120)}, 255), "
                    f"stop:0.25 rgba({min(255, r + 120)}, {min(255, g + 120)}, {min(255, b + 120)}, 255), "
                    f"stop:0.26 rgba({r}, {g}, {b}, 255), "
                    f"stop:0.75 rgba({r}, {g}, {b}, 255), "
                    f"stop:0.76 rgba({min(255, r + 120)}, {min(255, g + 120)}, {min(255, b + 120)}, 255), "
                    f"stop:1 rgba({min(255, r + 120)}, {min(255, g + 120)}, {min(255, b + 120)}, 255));"
                    f"border-width: 2px; border-style: solid;"
                )
            else:
                self.setStyleSheet(
                    f"border-color: qlineargradient("
                    f"spread:pad, x1:0 y1:0, x2:1 y2:0, "
                    f"stop:0 rgba({max(0, r - 75)}, {max(0, g - 75)}, {max(0, b - 75)}, 255), "
                    f"stop:0.25 rgba({max(0, r - 75)}, {max(0, g - 75)}, {max(0, b - 75)}, 255), "
                    f"stop:0.26 rgba({r}, {g}, {b}, 255), "
                    f"stop:0.74 rgba({r}, {g}, {b}, 255), "
                    f"stop:0.75 rgba({max(0, r - 75)}, {max(0, g - 75)}, {max(0, b - 75)}, 255), "
                    f"stop:1 rgba({max(0, r - 75)}, {max(0, g - 75)}, {max(0, b - 75)}, 255)); "
                    f"border-width: 2px; border-style: solid;"
                )
        elif model.selection_type is Selection.TERTIARY:
            if model.color.to_qt().lightnessF() < 0.25:
                self.setStyleSheet(
                    f"border-color: qlineargradient("
                    f"spread:pad, x1:0 y1:0, x2:1 y2:1, "
                    f"stop:0 rgba({min(255, r + 120)}, {min(255, g + 120)}, {min(255, b + 120)}, 255), "
                    f"stop:0.25 rgba({min(255, r + 120)}, {min(255, g + 120)}, {min(255, b + 120)}, 255), "
                    f"stop:0.26 rgba({r}, {g}, {b}, 255), "
                    f"stop:0.75 rgba({r}, {g}, {b}, 255), "
                    f"stop:0.76 rgba({min(255, r + 120)}, {min(255, g + 120)}, {min(255, b + 120)}, 255), "
                    f"stop:1 rgba({min(255, r + 120)}, {min(255, g + 120)}, {min(255, b + 120)}, 255));"
                    f"border-width: 2px; border-style: solid;"
                )
            else:
                self.setStyleSheet(
                    f"border-color: qlineargradient("
                    f"spread:pad, x1:0 y1:0, x2:1 y2:1, "
                    f"stop:0 rgba({max(0, r - 75)}, {max(0, g - 75)}, {max(0, b - 75)}, 255), "
                    f"stop:0.25 rgba({max(0, r - 75)}, {max(0, g - 75)}, {max(0, b - 75)}, 255), "
                    f"stop:0.26 rgba({r}, {g}, {b}, 255), "
                    f"stop:0.74 rgba({r}, {g}, {b}, 255), "
                    f"stop:0.75 rgba({max(0, r - 75)}, {max(0, g - 75)}, {max(0, b - 75)}, 255), "
                    f"stop:1 rgba({max(0, r - 75)}, {max(0, g - 75)}, {max(0, b - 75)}, 255)); "
                    f"border-width: 2px; border-style: solid;"
                )
        elif model.color.to_qt().lightnessF() < 0.25:
            self.setStyleSheet(
                f"border-color: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:0, "
                f"stop:0 rgba({model.color.red}, {model.color.green}, {model.color.blue}, 255), "
                f"stop:1 rgba(255, 255, 255, 255));"
                f"border-width: 2px; border-style: {generate_border(model.selection_type).to_qt_stylesheet()}"
            )
        else:
            self.setStyleSheet(
                f"border-color: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:0, "
                f"stop:0 rgba(0, 0, 0, 255), "
                f"stop:1 rgba({model.color.red}, {model.color.green}, {model.color.blue}, 255));"
                f"border-width: 2px; border-style: {generate_border(model.selection_type).to_qt_stylesheet()}"
            )

        self.update()


class ColorPicker(MouseAggregator, KeyHandler, UndoRedoExtendedForwarder, Widget):
    ROWS: ClassVar[int] = 4
    COLUMNS: ClassVar[int] = 16
    selected: int
    secondary_selection: int
    original_selection: int
    color_palette: ColorPalette
    size: Size
    color_selected: SignalInstance[Color]

    @attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
    class Model:
        selected: int = 0
        original_selection: int = 0
        secondary_selection: int = 0
        color_palette: ColorPalette = ColorPalette.from_default()
        button_size: Size = Size(24, 24)

        def __str__(self) -> str:
            return f"<{self.selected}, {self.secondary_selection}>"

    @property
    def aggregates(self) -> Sequence[MouseHandler | MouseAggregator]:
        return self._buttons

    def _handle_clicked(self, aggregate: MouseEventAggregate[ColorButton, MouseEvent]) -> None:
        prior: int = self.selected
        if aggregate.event.click == Click.LEFT_CLICK:
            self.selected = aggregate.index
            if aggregate.event.control:
                self.secondary_selection = self.selected
        elif aggregate.event.click == Click.RIGHT_CLICK:
            self.secondary_selection = aggregate.index
            if aggregate.event.control:
                self.selected = self.secondary_selection

        if prior != self.selected:
            self.color_selected.emit(self.color_palette.colors[aggregate.index])

    def _handle_wheel_event(self, aggregate: MouseEventAggregate[ColorButton, MouseWheelEvent]) -> None:
        prior: int = self.selected
        if aggregate.event.control or aggregate.event.orientation == Orientation.HORIZONTAL:
            if 0 <= self.selected + (int(aggregate.event.steps) * self.COLUMNS) < self.ROWS * self.COLUMNS:
                self.selected = self.selected + (int(aggregate.event.steps) * self.COLUMNS)
        elif 0 <= self.selected + int(aggregate.event.steps) < self.ROWS * self.COLUMNS:
            self.selected = self.selected + int(aggregate.event.steps)

        if prior != self.selected:
            self.color_selected.emit(self.color_palette.colors[self.selected])

    def _handle_undo_key_event(self) -> None:
        super()._handle_undo_key_event()
        self.color_selected.emit(self.color_palette.colors[self.selected])

    def _handle_redo_key_event(self) -> None:
        super()._handle_redo_key_event()
        self.color_selected.emit(self.color_palette.colors[self.selected])

    def _handle_swap_key_event(self) -> None:
        self.selected, self.secondary_selection = self.secondary_selection, self.selected
        self.color_selected.emit(self.color_palette.colors[self.selected])

    def initialize_state(self, model: Model, *args, **kwargs) -> None:
        super().initialize_state(model, *args, **kwargs)
        self.register_key_sequence(KeySequence(Key.ALT, Modifier.ALT), self._handle_swap_key_event)

        grid_layout: QGridLayout = QGridLayout(self)
        grid_layout.setSpacing(0)

        self._buttons: list[ColorButton] = []
        for row in range(self.ROWS):
            for column in range(self.COLUMNS):
                button = ColorButton(
                    ColorButton.Model(model.color_palette.colors[row * self.COLUMNS + column], model.button_size),
                    parent=self,
                )
                button.setLineWidth(0)
                self._buttons.append(button)
                grid_layout.addWidget(button, row, column)
        self._buttons[model.secondary_selection].selection_type = Selection.SECONDARY
        self._buttons[model.selected].selection_type = Selection.PRIMARY
        self.connect_aggregates()
        self.clicked.connect(self._handle_clicked)
        self.wheel_moved.connect(self._handle_wheel_event)

    def change_state(self, model: Model) -> None:
        super().change_state(model)
        undo_peak = self.peak_undo
        redo_peak = self.peak_redo

        for index, button in enumerate(self._buttons):
            if model.selected == index:
                button.selection_type = Selection.PRIMARY
            elif model.secondary_selection == index:
                button.selection_type = Selection.SECONDARY
            elif model.original_selection == index:
                button.selection_type = Selection.TERTIARY
            elif undo_peak is not None and (undo_peak.selected == index or undo_peak.secondary_selection == index):
                button.selection_type = Selection.UNDO
            elif redo_peak is not None and (redo_peak.selected == index or redo_peak.secondary_selection == index):
                button.selection_type = Selection.REDO
            elif button.selection_type is not Selection.NONE:
                button.selection_type = Selection.NONE

        self.update()


class ColorPickerDialog(Dialog, MouseAggregator, KeyHandler):
    active_palette_group: int
    active_palette: int
    active_color: int
    original_palette_group: PaletteGroup
    palette_group: PaletteGroup
    palette_group_changed: SignalInstance[PaletteGroup]
    dialog_finished: SignalInstance[PaletteGroup]

    @attrs(slots=True, auto_attribs=True, frozen=True, eq=True, hash=True)
    class Model:
        active_palette_group: int = 0
        active_palette: int = 0
        active_color: int = 0
        original_palette_group: PaletteGroup = PaletteGroup.as_empty()
        palette_group: PaletteGroup = PaletteGroup.as_empty()

        def __str__(self) -> str:
            return f"<{self.palette_group}>"

    @property
    def palette(self) -> Palette:
        return self.palette_group[self.active_palette]

    @palette.setter
    def palette(self, palette: Palette) -> None:
        self.palette_group.evolve_palettes(self.active_palette, palette)

    @property
    def color(self) -> Color:
        return self.palette.color_from_index(self.palette[self.active_color])

    @color.setter
    def color(self, color: Color) -> None:
        self.palette.evolve_color_index()

    def _forward_dialog_exit(self, dialog_event: DialogEvent[int]) -> None:
        if dialog_event.suggestion is not None:
            self.dialog_finished.emit(self.palette_group)
        self.done(0)

    def _color_selected(self, color: Color) -> None:
        self.palette_group.evolve_palettes(self.active_palette, self.palette_group[self.active_palette])

    def _change_active_palette(self, index: int) -> None:
        self.active_palette = index

    def initialize_state(self, model: Model, *args, **kwargs) -> None:
        super().initialize_state(model, *args, **kwargs)

        self.palette_tab = TabBar(BaseModel(), self, tabs=["1", "2", "3", "4"])
        self.palette_tab.tab_selected.connect(self._change_active_palette)

        grid_layout: QGridLayout = QGridLayout()
        grid_layout.setSpacing(0)

        self.color_picker = ColorPicker(
            ColorPicker.Model(  # type: ignore
                model.active_color,
                model.active_color,
                model.active_color,
                model.palette_group[model.active_palette].color_palette,
            )
        )
        self.color_picker.color_selected

        self.dialog_options: DialogOption[int] = DialogOption(
            BaseModel(),
            buttons=[DialogControl.ACCEPT, DialogControl.REJECT],
            accept_suggestion=lambda: self.palette_group,
            reject_suggestion=lambda: self.original_palette_group,
        )
        self.dialog_options.dialog_event.connect(self._forward_dialog_exit)

        layout = QVBoxLayout(self)
        layout.addWidget(self.palette_tab, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.color_picker, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.dialog_options, alignment=Qt.AlignmentFlag.AlignCenter)


class PaletteWidget(MouseAggregator, Widget):
    Model = Palette  # type: ignore
    model: Palette

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.model})"

    @property
    def aggregates(self) -> Sequence[MouseHandler | MouseAggregator]:
        return self._buttons

    def initialize_state(self, model: Palette, *args, **kwargs) -> None:
        super().initialize_state(model, *args, **kwargs)

        layout: QHBoxLayout = QHBoxLayout(self)
        layout.setContentsMargins(1, 2, 0, 2)

        self._buttons: list[ColorButton] = [
            ColorButton(ColorButton.Model(Color.from_qt(color)), parent=self) for color in model.colors
        ]

        for button in self._buttons:
            layout.addWidget(button)

        self.connect_aggregates()

    def change_state(self, model: Palette) -> None:
        for idx, color in enumerate(model.colors):
            if self._buttons[idx].color != Color.from_qt(color):
                self._buttons[idx].color = Color.from_qt(color)


class PaletteGroupWidget(MouseAggregator, Widget):
    Model = PaletteGroup  # type: ignore
    model: PaletteGroup

    @property
    def aggregates(self) -> Sequence[MouseHandler | MouseAggregator]:
        return self._palette_widgets

    def initialize_state(self, model: PaletteGroup, change_colors: bool = True, *args, **kwargs) -> None:
        super().initialize_state(model, *args, **kwargs)

        layout: QHBoxLayout = QHBoxLayout(self)
        layout.setContentsMargins(1, 2, 0, 2)

        self._palette_widgets: list[PaletteWidget] = [
            PaletteWidget(palette) for palette in model.palettes  # type: ignore
        ]

        for widget in self._palette_widgets:
            layout.addWidget(widget)

        self.connect_aggregates()
        if change_colors:
            self.clicked.connect(self.handle_clicked)

    def handle_clicked(
        self, aggregate: MouseEventAggregate[PaletteWidget, MouseEventAggregate[ColorButton, MouseEvent]]
    ):
        def change_palette_group(palette_group: PaletteGroup) -> None:
            print("changing", palette_group)
            self.model = palette_group

        picker = ColorPickerDialog(
            ColorPickerDialog.Model(0, aggregate.index, aggregate.event.index, self.model),  # type: ignore
            parent=self,
        )
        picker.palette_group_changed.connect(change_palette_group)
        picker.dialog_finished.connect(change_palette_group)
        picker.exec()

    def change_state(self, model: PaletteGroup) -> None:
        for idx, palette in enumerate(model.palettes):
            if self._palette_widgets[idx].model != palette:
                self._palette_widgets[idx].model = palette
