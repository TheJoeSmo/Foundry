from pytest import fixture

from foundry.gui.LevelStartEditor import (
    LevelStartDisplay,
    LevelStartEditor,
    LevelStartState,
)


@fixture
def warp_info() -> LevelStartState:
    return LevelStartState(0, 1, 2)


@fixture
def warp_display() -> LevelStartDisplay:
    return LevelStartDisplay(None, 0, 1, 2)


@fixture
def warp_editor(warp_info):
    return LevelStartEditor(None, warp_info)


def test_warp_state_initialization():
    LevelStartState(0, 1, 2)


def test_warp_state_equality():
    assert LevelStartState(0, 1, 2) == LevelStartState(0, 1, 2)


def test_warp_state_inequality():
    assert LevelStartState(0, 1, 2) != LevelStartState(2, 1, 0)


def test_warp_state_inequality_other():
    assert LevelStartState(0, 1, 2) != 1


def test_initialization(qtbot, warp_info):
    LevelStartEditor(None, warp_info)


def test_normal_equality(qtbot, warp_info):
    assert LevelStartEditor(None, warp_info) == LevelStartEditor(None, warp_info)


def test_normal_inequality(qtbot):  # sourcery skip: de-morgan
    assert LevelStartEditor(None, LevelStartState(0, 1, 2)) != LevelStartEditor(None, LevelStartState(2, 1, 0))


def test_equality_undo(qtbot, warp_info):
    editor1 = LevelStartEditor(None, warp_info)
    editor2 = LevelStartEditor(None, warp_info)
    editor1.state = LevelStartState(2, 1, 0)
    editor1.undo()
    assert editor1 != editor2

    editor2.state = LevelStartState(2, 1, 0)

    assert editor1 != editor2

    editor2.undo()
    assert editor1 == editor2


def test_equality_redo(qtbot, warp_info):
    editor1 = LevelStartEditor(None, warp_info)
    editor2 = LevelStartEditor(None, warp_info)
    editor1.state = LevelStartState(2, 1, 0)
    editor1.undo()
    editor1.redo()
    assert editor1 != editor2

    editor2.state = LevelStartState(2, 1, 0)

    assert editor1 == editor2

    editor2.undo()
    editor2.redo()
    assert editor1 == editor2


def test_inequality_other(qtbot, warp_editor):
    assert warp_editor != 3


def test_x_position_update_x_position_changed(qtbot, warp_info):
    editor = LevelStartEditor(None, warp_info)

    with qtbot.waitSignal(editor.x_position_changed, timeout=100):
        editor.x_position = 3

    assert editor.x_position == 3
    assert editor.state.x_position == 3


def test_x_position_update_state_changed(qtbot, warp_info):
    editor = LevelStartEditor(None, warp_info)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.x_position = 3

    assert editor.x_position == 3
    assert editor.state.x_position == 3


def test_x_position_undo_x_position_changed(qtbot, warp_info):
    editor = LevelStartEditor(None, warp_info)
    expected = editor.x_position
    editor.x_position = 3

    with qtbot.waitSignal(editor.x_position_changed, timeout=100):
        editor.undo()

    assert editor.x_position == expected
    assert editor.state.x_position == expected


def test_x_position_undo_x_position_state_changed(qtbot, warp_info):
    editor = LevelStartEditor(None, warp_info)
    expected = editor.x_position
    editor.x_position = 3

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.x_position == expected
    assert editor.state.x_position == expected


def test_x_position_redo_x_position_changed(qtbot, warp_info):
    editor = LevelStartEditor(None, warp_info)
    editor.x_position = 3
    editor.undo()

    with qtbot.waitSignal(editor.x_position_changed, timeout=100):
        editor.redo()

    assert editor.x_position == 3
    assert editor.state.x_position == 3


def test_x_position_redo_x_position_state_changed(qtbot, warp_info):
    editor = LevelStartEditor(None, warp_info)
    editor.x_position = 3
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.x_position == 3
    assert editor.state.x_position == 3


def test_y_position_update_y_position_changed(qtbot, warp_info):
    editor = LevelStartEditor(None, warp_info)

    with qtbot.waitSignal(editor.y_position_changed, timeout=100):
        editor.y_position = 3

    assert editor.y_position == 3
    assert editor.state.y_position == 3


def test_y_position_update_state_changed(qtbot, warp_info):
    editor = LevelStartEditor(None, warp_info)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.y_position = 3

    assert editor.y_position == 3
    assert editor.state.y_position == 3


def test_y_position_undo_y_position_changed(qtbot, warp_info):
    editor = LevelStartEditor(None, warp_info)
    expected = editor.y_position
    editor.y_position = 3

    with qtbot.waitSignal(editor.y_position_changed, timeout=100):
        editor.undo()

    assert editor.y_position == expected
    assert editor.state.y_position == expected


def test_y_position_undo_state_changed(qtbot, warp_info):
    editor = LevelStartEditor(None, warp_info)
    expected = editor.y_position
    editor.y_position = 3

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.y_position == expected
    assert editor.state.y_position == expected


def test_y_position_redo_y_position_changed(qtbot, warp_info):
    editor = LevelStartEditor(None, warp_info)
    editor.y_position = 3
    editor.undo()

    with qtbot.waitSignal(editor.y_position_changed, timeout=100):
        editor.redo()

    assert editor.y_position == 3
    assert editor.state.y_position == 3


def test_y_position_redo_state_changed(qtbot, warp_info):
    editor = LevelStartEditor(None, warp_info)
    editor.y_position = 3
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.y_position == 3
    assert editor.state.y_position == 3


def test_action_update_action_changed(qtbot, warp_info):
    editor = LevelStartEditor(None, warp_info)

    with qtbot.waitSignal(editor.action_changed, timeout=100):
        editor.action = 3

    assert editor.action == 3
    assert editor.state.action == 3


def test_action_update_state_changed(qtbot, warp_info):
    editor = LevelStartEditor(None, warp_info)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.action = 3

    assert editor.action == 3
    assert editor.state.action == 3


def test_action_undo_action_changed(qtbot, warp_info):
    editor = LevelStartEditor(None, warp_info)
    expected = editor.action
    editor.action = 3

    with qtbot.waitSignal(editor.action_changed, timeout=100):
        editor.undo()

    assert editor.action == expected
    assert editor.state.action == expected


def test_action_undo_state_changed(qtbot, warp_info):
    editor = LevelStartEditor(None, warp_info)
    expected = editor.action
    editor.action = 3

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.action == expected
    assert editor.state.action == expected


def test_action_redo_action_changed(qtbot, warp_info):
    editor = LevelStartEditor(None, warp_info)
    editor.action = 7
    editor.undo()

    with qtbot.waitSignal(editor.action_changed, timeout=100):
        editor.redo()

    assert editor.action == 7
    assert editor.state.action == 7


def test_action_redo_state_changed(qtbot, warp_info):
    editor = LevelStartEditor(None, warp_info)
    editor.action = 7
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.action == 7
    assert editor.state.action == 7


def test_display_initialization(qtbot):
    LevelStartDisplay(None, 0, 1, 2)


def test_display_equality(qtbot):
    assert LevelStartDisplay(None, 0, 1, 2) == LevelStartDisplay(None, 0, 1, 2)


def test_display_inequality(qtbot):
    assert LevelStartDisplay(None, 0, 1, 2) != LevelStartDisplay(None, 2, 1, 0)


def test_display_other_inequality(qtbot):
    assert LevelStartDisplay(None, 0, 1, 2) != 3


def test_display_get_x_position(qtbot):
    display = LevelStartDisplay(None, 0, 1, 2)
    assert 0 == display.x_position


def test_display_set_x_position(qtbot, warp_display: LevelStartDisplay):
    warp_display.x_position = 3
    assert 3 == warp_display.x_position


def test_display_get_y_position(qtbot):
    display = LevelStartDisplay(None, 0, 1, 2)
    assert 1 == display.y_position


def test_display_set_y_position(qtbot, warp_display: LevelStartDisplay):
    warp_display.y_position = 3
    assert 3 == warp_display.y_position


def test_display_get_eaction(qtbot):
    display = LevelStartDisplay(None, 0, 1, 2)
    assert 2 == display.action


def test_display_set_action(qtbot, warp_display: LevelStartDisplay):
    warp_display.action = 3
    assert 3 == warp_display.action


def test_set_x_position(qtbot, warp_editor: LevelStartEditor):
    warp_editor._display.x_position = 3
    assert 3 == warp_editor.x_position


def test_set_y_position(qtbot, warp_editor: LevelStartEditor):
    warp_editor._display.y_position = 3
    assert 3 == warp_editor.y_position


def test_set_action(qtbot, warp_editor: LevelStartEditor):
    warp_editor._display.action = 3
    assert 3 == warp_editor.action


def test_set_x_position_value(qtbot, warp_editor: LevelStartEditor):
    warp_editor._display.x_position_editor.setCurrentIndex(3)
    assert 3 == warp_editor.x_position


def test_set_y_position_value(qtbot, warp_editor: LevelStartEditor):
    warp_editor._display.y_position_editor.setCurrentIndex(3)
    assert 3 == warp_editor.y_position


def test_set_action_value(qtbot, warp_editor: LevelStartEditor):
    warp_editor._display.action_editor.setCurrentIndex(3)
    assert 3 == warp_editor.action
