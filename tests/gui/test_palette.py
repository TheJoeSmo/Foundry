from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QMainWindow
from pytest import fixture

from foundry.core.geometry import Size
from foundry.core.palette import Color, ColorPalette, Palette
from foundry.gui.palette import (
    ColorButtonState,
    ColorButtonWidget,
    ColorSelector,
    PaletteDisplay,
    PaletteEditorWidget,
    PaletteWidget,
)


@fixture
def color() -> Color:
    return Color(0, 1, 2, 3)


@fixture
def alternative_color() -> Color:
    return Color(4, 5, 6, 7)


@fixture
def size() -> Size:
    return Size(32, 32)


@fixture
def alternative_size() -> Size:
    return Size(64, 64)


@fixture
def color_palette() -> ColorPalette:
    return ColorPalette((Color(0, 1, 2), Color(3, 4, 5), Color(6, 7, 8, 9)))


@fixture
def palette(color_palette: ColorPalette) -> Palette:
    return Palette((0, 2, 1), color_palette)


@fixture
def alternative_palette(color_palette: ColorPalette) -> Palette:
    return Palette((2, 1, 0), color_palette)


@fixture
def color_button_model() -> ColorButtonState:
    return ColorButtonState()


@fixture(scope="session")
def temp_app():
    yield QMainWindow()


def test_color_button_model_initialization_default():
    ColorButtonState()


def test_color_button_model_initialization_normal(color: Color, size: Size):
    ColorButtonState(color, size, True)


def test_color_button_model_equality(color: Color, size: Size):
    assert ColorButtonState(color, size, True) == ColorButtonState(color, size, True)


def test_color_button_model_inequality_from_color(color: Color, alternative_color: Color, size: Size):
    assert ColorButtonState(color, size, True) != ColorButtonState(alternative_color, size, True)


def test_color_button_model_inequality_from_size(color: Color, size: Size, alternative_size: Size):
    assert ColorButtonState(color, size, True) != ColorButtonState(color, alternative_size, True)


def test_color_button_model_inequality_from_selected(color: Color, size: Size):
    assert ColorButtonState(color, size, True) != ColorButtonState(color, size, False)


def test_color_button_model_inequality_from_other():
    assert ColorButtonState() != 1


def test_color_button_initialization_default(qtbot):
    ColorButtonWidget(None)


def test_color_button_initialization_normal(qtbot, color: Color, size: Size):
    ColorButtonWidget(None, color, size, False)


def test_color_button_equality(color: Color, size: Size):
    assert ColorButtonWidget(None, color, size, False) == ColorButtonWidget(None, color, size, False)


def test_color_button_inequality_color(color: Color, alternative_color: Color, size: Size):
    assert ColorButtonWidget(None, color, size, False) != ColorButtonWidget(None, alternative_color, size, False)


def test_color_button_inequality_size(color: Color, size: Size, alternative_size: Size):
    assert ColorButtonWidget(None, color, size, False) != ColorButtonWidget(None, color, alternative_size, False)


def test_color_butotn_inequality_selected(color: Color, size: Size):
    assert ColorButtonWidget(None, color, size, False) != ColorButtonWidget(None, color, size, True)


def test_color_button_equality_undo(color: Color, alternative_color: Color, size: Size, alternative_size: Size):
    button1 = ColorButtonWidget(None, color, size, True)
    button2 = ColorButtonWidget(None, color, size, True)
    button1.state = ColorButtonState(alternative_color, alternative_size, False)
    button1.undo()
    assert button1 != button2

    button2.state = ColorButtonState(alternative_color, alternative_size, False)

    assert button1 != button2

    button2.undo()
    assert button1 == button2


def test_color_button_equality_redo(color: Color, alternative_color: Color, size: Size, alternative_size: Size):
    button1 = ColorButtonWidget(None, color, size, True)
    button2 = ColorButtonWidget(None, color, size, True)
    button1.state = ColorButtonState(alternative_color, alternative_size, False)
    button1.undo()
    button1.redo()
    assert button1 != button2

    button2.state = ColorButtonState(alternative_color, alternative_size, False)

    assert button1 == button2

    button2.undo()
    button2.redo()
    assert button1 == button2


def test_color_button_inequality_other():
    assert ColorButtonState() != 5


def test_color_button_color_update_color_changed(qtbot, color: Color, alternative_color: Color, size: Size):
    button = ColorButtonWidget(None, color, size, True)

    with qtbot.waitSignal(button.color_changed, timeout=100):
        button.color = alternative_color

    assert button.color == alternative_color
    assert button.state.color == alternative_color


def test_color_button_color_undo_color_changed(qtbot, color: Color, alternative_color: Color, size: Size):
    button = ColorButtonWidget(None, color, size, True)
    expected = button.color
    button.color = alternative_color

    with qtbot.waitSignal(button.color_changed, timeout=100):
        button.undo()

    assert button.color == expected
    assert button.state.color == expected


def test_color_button_color_redo_color_changed(qtbot, color: Color, alternative_color: Color, size: Size):
    button = ColorButtonWidget(None, color, size, True)
    button.color = alternative_color
    button.undo()

    with qtbot.waitSignal(button.color_changed, timeout=100):
        button.redo()

    assert button.color == alternative_color
    assert button.state.color == alternative_color


def test_color_button_size_update_size_changed(qtbot, color: Color, size: Size, alternative_size: Size):
    button = ColorButtonWidget(None, color, size, True)

    with qtbot.waitSignal(button.size_changed, timeout=100):
        button.size_ = alternative_size

    assert button.size_ == alternative_size
    assert button.state.size == alternative_size


def test_color_button_size_undo_size_changed(qtbot, color: Color, size: Size, alternative_size: Size):
    button = ColorButtonWidget(None, color, size, True)
    expected = button.size_
    button.size_ = alternative_size

    with qtbot.waitSignal(button.size_changed, timeout=100):
        button.undo()

    assert button.size_ == expected
    assert button.state.size == expected


def test_color_button_size_redo_size_changed(qtbot, color: Color, size: Size, alternative_size: Size):
    button = ColorButtonWidget(None, color, size, True)
    button.size_ = alternative_size
    button.undo()

    with qtbot.waitSignal(button.size_changed, timeout=100):
        button.redo()

    assert button.size_ == alternative_size
    assert button.state.size == alternative_size


def test_color_button_selected_update_selected_changed(qtbot, color: Color, size: Size):
    button = ColorButtonWidget(None, color, size, True)

    with qtbot.waitSignal(button.selected_changed, timeout=100):
        button.selected = False

    assert not button.selected
    assert not button.state.selected


def test_color_button_selected_undo_selected_changed(qtbot, color: Color, size: Size):
    button = ColorButtonWidget(None, color, size, True)
    expected = button.selected
    button.selected = False

    with qtbot.waitSignal(button.selected_changed, timeout=100):
        button.undo()

    assert button.selected == expected
    assert button.state.selected == expected


def test_color_button_selected_redo_selected_changed(qtbot, color: Color, size: Size):
    button = ColorButtonWidget(None, color, size, True)
    button.selected = False
    button.undo()

    with qtbot.waitSignal(button.selected_changed, timeout=100):
        button.redo()

    assert not button.selected
    assert not button.state.selected


def test_color_selector_initialization_defaults():
    ColorSelector(None)


def test_color_selector_initialization_normal(size: Size, color_palette: ColorPalette):
    ColorSelector(None, title="test", size=size, color_palette=color_palette, selected_button=1, rows=1, columns=3)


def test_color_selector_selecting_button(qtbot, size: Size, color_palette: ColorPalette):
    selector = ColorSelector(
        None, title="test", size=size, color_palette=color_palette, selected_button=1, rows=1, columns=3
    )

    qtbot.mouseClick(selector._buttons[0], Qt.LeftButton)

    assert 0 == selector.last_selected_color_index


def test_color_selector_finish_dialog(qtbot, size: Size, color_palette: ColorPalette):
    selector = ColorSelector(
        None, title="test", size=size, color_palette=color_palette, selected_button=1, rows=1, columns=3
    )

    qtbot.mouseClick(selector._buttons[0], Qt.LeftButton)

    with qtbot.waitSignal(selector.ok_clicked, timeout=100, check_params_cb=lambda value: value == 0):
        selector._on_dialog(selector._dialog.button(QDialogButtonBox.Ok))


def test_palette_display_initialization(temp_app, palette: Palette):
    PaletteDisplay(temp_app, palette)


def test_palette_display_palette(temp_app, palette: Palette):
    assert PaletteDisplay(temp_app, palette).palette == palette


def test_palette_display_set_palette(temp_app, palette: Palette, alternative_palette: Palette):
    display = PaletteDisplay(temp_app, palette)
    display.palette = alternative_palette

    assert display.palette != palette
    assert display.palette == alternative_palette


def test_palette_display_button_clicked(qtbot, temp_app, palette: Palette):
    display = PaletteDisplay(temp_app, palette)

    with qtbot.waitSignal(display.button_clicked, timeout=100, check_params_cb=lambda value: value == 1):
        qtbot.mouseClick(display.buttons[1], Qt.LeftButton)


def test_palette_widget_initialization(palette: Palette):
    PaletteWidget(None, palette)


def test_palette_widget_equality(palette: Palette):
    assert PaletteWidget(None, palette) == PaletteWidget(None, palette)


def test_palette_widget_inequality_from_palette(palette: Palette, alternative_palette: Palette):
    assert PaletteWidget(None, palette) != PaletteWidget(None, alternative_palette)


def test_palette_widget_equality_undo(palette: Palette, alternative_palette: Palette):
    widget1 = PaletteWidget(None, palette)
    widget2 = PaletteWidget(None, palette)
    widget1.palette = alternative_palette
    widget1.undo()
    assert widget1 != widget2

    widget2.palette = alternative_palette

    assert widget1 != widget2

    widget2.undo()

    assert widget1 == widget2


def test_palette_widget_equality_redo(palette: Palette, alternative_palette: Palette):
    widget1 = PaletteWidget(None, palette)
    widget2 = PaletteWidget(None, palette)
    widget1.palette = alternative_palette
    widget1.undo()
    widget1.redo()
    assert widget1 != widget2

    widget2.palette = alternative_palette

    assert widget1 == widget2

    widget2.undo()
    widget2.redo()

    assert widget1 == widget2


def test_palette_widget_inequality_from_other(palette: Palette):
    assert PaletteWidget(None, palette) != 1


def test_palette_widget_palette(palette: Palette):
    widget = PaletteWidget(None, palette)

    assert palette == widget.palette


def test_palette_widget_set_palette(qtbot, palette: Palette, alternative_palette: Palette):
    widget = PaletteWidget(None, palette)

    with qtbot.waitSignal(
        widget.palette_changed, timeout=100, check_params_cb=lambda value: value == alternative_palette
    ):
        widget.palette = alternative_palette

    assert widget.palette == alternative_palette
    assert widget._display.palette == alternative_palette


def test_palette_widget_undo_palette(qtbot, palette: Palette, alternative_palette: Palette):
    widget = PaletteWidget(None, palette)
    widget.palette = alternative_palette

    with qtbot.waitSignal(widget.palette_changed, timeout=100, check_params_cb=lambda value: value == palette):
        widget.undo()

    assert widget.palette == palette
    assert widget._display.palette == palette


def test_palette_widget_redo_palette(qtbot, palette: Palette, alternative_palette: Palette):
    widget = PaletteWidget(None, palette)
    widget.palette = alternative_palette
    widget.undo()

    with qtbot.waitSignal(
        widget.palette_changed, timeout=100, check_params_cb=lambda value: value == alternative_palette
    ):
        widget.redo()

    assert widget.palette == alternative_palette
    assert widget._display.palette == alternative_palette


def test_palette_editor_widget_initialization(palette: Palette):
    PaletteEditorWidget(None, palette)


def test_palette_editor_widget_equality(palette: Palette):
    assert PaletteEditorWidget(None, palette) == PaletteEditorWidget(None, palette)


def test_palette_editor_widget_inequality_from_palette(palette: Palette, alternative_palette: Palette):
    assert PaletteEditorWidget(None, palette) != PaletteEditorWidget(None, alternative_palette)


def test_palette_editor_widget_equality_undo(palette: Palette, alternative_palette: Palette):
    widget1 = PaletteEditorWidget(None, palette)
    widget2 = PaletteEditorWidget(None, palette)
    widget1.palette = alternative_palette
    widget1.undo()
    assert widget1 != widget2

    widget2.palette = alternative_palette

    assert widget1 != widget2

    widget2.undo()

    assert widget1 == widget2


def test_palette_editor_widget_equality_redo(palette: Palette, alternative_palette: Palette):
    widget1 = PaletteEditorWidget(None, palette)
    widget2 = PaletteEditorWidget(None, palette)
    widget1.palette = alternative_palette
    widget1.undo()
    widget1.redo()
    assert widget1 != widget2

    widget2.palette = alternative_palette

    assert widget1 == widget2

    widget2.undo()
    widget2.redo()

    assert widget1 == widget2


def test_palette_editor_widget_inequality_from_other(palette: Palette):
    assert PaletteEditorWidget(None, palette) != 1


def test_palette_editor_widget_palette(palette: Palette):
    widget = PaletteEditorWidget(None, palette)

    assert palette == widget.palette


def test_palette_editor_widget_set_palette(qtbot, palette: Palette, alternative_palette: Palette):
    widget = PaletteEditorWidget(None, palette)

    with qtbot.waitSignal(
        widget.palette_changed, timeout=100, check_params_cb=lambda value: value == alternative_palette
    ):
        widget.palette = alternative_palette

    assert widget.palette == alternative_palette
    assert widget._display.palette == alternative_palette


def test_palette_editor_widget_undo_palette(qtbot, palette: Palette, alternative_palette: Palette):
    widget = PaletteEditorWidget(None, palette)
    widget.palette = alternative_palette

    with qtbot.waitSignal(widget.palette_changed, timeout=100, check_params_cb=lambda value: value == palette):
        widget.undo()

    assert widget.palette == palette
    assert widget._display.palette == palette


def test_palette_editor_widget_redo_palette(qtbot, palette: Palette, alternative_palette: Palette):
    widget = PaletteEditorWidget(None, palette)
    widget.palette = alternative_palette
    widget.undo()

    with qtbot.waitSignal(
        widget.palette_changed, timeout=100, check_params_cb=lambda value: value == alternative_palette
    ):
        widget.redo()

    assert widget.palette == alternative_palette
    assert widget._display.palette == alternative_palette


class FakeColorSelector(ColorSelector):
    @property
    def last_selected_color_index(self) -> int:
        return len(self._buttons)

    def exec_(self):
        return QDialog.Accepted


def _generate_color_selector(self) -> ColorSelector:
    return FakeColorSelector(self)


def test_palette_editor_widget_from_color_selector(qtbot, palette: Palette):
    widget = PaletteEditorWidget(None, palette)

    method = PaletteEditorWidget._generate_color_selector  # store so we can restore it afterwards.
    PaletteEditorWidget._generate_color_selector = _generate_color_selector

    with qtbot.waitSignal(widget.palette_changed, timeout=100, check_params_cb=lambda value: palette != value):
        qtbot.mouseClick(widget._display.buttons[1], Qt.LeftButton)

    PaletteEditorWidget._generate_color_selector = method  # restore the actual method so we don't mess up tests.
