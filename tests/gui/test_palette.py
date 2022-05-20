from pytest import fixture

from foundry.core.geometry import Size
from foundry.core.palette import Color
from foundry.gui.palette import ColorButtonState, ColorButtonWidget


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
def color_button_model() -> ColorButtonState:
    return ColorButtonState()


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


def test_color_button_equality(qtbot, color: Color, size: Size):
    assert ColorButtonWidget(None, color, size, False) == ColorButtonWidget(None, color, size, False)


def test_color_button_inequality_color(qtbot, color: Color, alternative_color: Color, size: Size):
    assert ColorButtonWidget(None, color, size, False) != ColorButtonWidget(None, alternative_color, size, False)


def test_color_button_inequality_size(qtbot, color: Color, size: Size, alternative_size: Size):
    assert ColorButtonWidget(None, color, size, False) != ColorButtonWidget(None, color, alternative_size, False)


def test_color_butotn_inequality_selected(qtbot, color: Color, size: Size):
    assert ColorButtonWidget(None, color, size, False) != ColorButtonWidget(None, color, size, True)


def test_color_button_equality_undo(qtbot, color: Color, alternative_color: Color, size: Size, alternative_size: Size):
    button1 = ColorButtonWidget(None, color, size, True)
    button2 = ColorButtonWidget(None, color, size, True)
    button1.state = ColorButtonState(alternative_color, alternative_size, False)
    button1.undo()
    assert button1 != button2

    button2.state = ColorButtonState(alternative_color, alternative_size, False)

    assert button1 != button2

    button2.undo()
    assert button1 == button2


def test_color_button_equality_redo(qtbot, color: Color, alternative_color: Color, size: Size, alternative_size: Size):
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


def test_color_button_inequality_other(qtbot):
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
