from pytest import fixture

from foundry.gui.LevelDataEditor import (
    LevelDataDisplay,
    LevelDataEditor,
    LevelDataState,
)


@fixture
def level_data() -> LevelDataState:
    return LevelDataState(0, 1, 2, 3, True, False)


@fixture
def data_display() -> LevelDataDisplay:
    return LevelDataDisplay(None, 0, 1, 2, 3, True, False)


@fixture
def data_editor(level_data):
    return LevelDataEditor(None, level_data)


def test_warp_state_initialization():
    LevelDataState(0, 1, 2, 3, True, False)


def test_warp_state_equality():
    assert LevelDataState(0, 1, 2, 3, True, False) == LevelDataState(0, 1, 2, 3, True, False)


def test_warp_state_inequality():
    assert LevelDataState(0, 1, 2, 3, True, False) != LevelDataState(3, 2, 1, 0, False, True)


def test_warp_state_inequality_other():
    assert LevelDataState(0, 1, 2, 3, True, False) != 1


def test_initialization(qtbot, level_data):
    LevelDataEditor(None, level_data)


def test_normal_equality(qtbot, level_data):
    assert LevelDataEditor(None, level_data) == LevelDataEditor(None, level_data)


def test_normal_inequality(qtbot):  # sourcery skip: de-morgan
    assert LevelDataEditor(None, LevelDataState(0, 1, 2, 3, True, False)) != LevelDataEditor(
        None, LevelDataState(3, 2, 1, 0, False, True)
    )


def test_equality_undo(qtbot, level_data):
    editor1 = LevelDataEditor(None, level_data)
    editor2 = LevelDataEditor(None, level_data)
    editor1.state = LevelDataState(3, 2, 1, 0, True, False)
    editor1.undo()
    assert editor1 != editor2

    editor2.state = LevelDataState(3, 2, 1, 0, True, False)

    assert editor1 != editor2

    editor2.undo()
    assert editor1 == editor2


def test_equality_redo(qtbot, level_data):
    editor1 = LevelDataEditor(None, level_data)
    editor2 = LevelDataEditor(None, level_data)
    editor1.state = LevelDataState(3, 2, 1, 0, True, False)
    editor1.undo()
    editor1.redo()
    assert editor1 != editor2

    editor2.state = LevelDataState(3, 2, 1, 0, True, False)

    assert editor1 == editor2

    editor2.undo()
    editor2.redo()
    assert editor1 == editor2


def test_inequality_other(qtbot, data_editor):
    assert data_editor != 3


def test_level_length_update_level_length_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)

    with qtbot.waitSignal(editor.level_length_changed, timeout=100):
        editor.level_length = 3

    assert editor.level_length == 3
    assert editor.state.level_length == 3


def test_level_length_update_state_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.level_length = 3

    assert editor.level_length == 3
    assert editor.state.level_length == 3


def test_level_length_undo_level_length_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    expected = editor.level_length
    editor.level_length = 3

    with qtbot.waitSignal(editor.level_length_changed, timeout=100):
        editor.undo()

    assert editor.level_length == expected
    assert editor.state.level_length == expected


def test_level_length_undo_level_length_state_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    expected = editor.level_length
    editor.level_length = 3

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.level_length == expected
    assert editor.state.level_length == expected


def test_level_length_redo_level_length_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    editor.level_length = 3
    editor.undo()

    with qtbot.waitSignal(editor.level_length_changed, timeout=100):
        editor.redo()

    assert editor.level_length == 3
    assert editor.state.level_length == 3


def test_level_length_redo_level_length_state_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    editor.level_length = 3
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.level_length == 3
    assert editor.state.level_length == 3


def test_music_update_music_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)

    with qtbot.waitSignal(editor.music_changed, timeout=100):
        editor.music = 3

    assert editor.music == 3
    assert editor.state.music == 3


def test_music_update_state_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.music = 3

    assert editor.music == 3
    assert editor.state.music == 3


def test_music_undo_music_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    expected = editor.music
    editor.music = 3

    with qtbot.waitSignal(editor.music_changed, timeout=100):
        editor.undo()

    assert editor.music == expected
    assert editor.state.music == expected


def test_music_undo_state_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    expected = editor.music
    editor.music = 3

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.music == expected
    assert editor.state.music == expected


def test_music_redo_music_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    editor.music = 3
    editor.undo()

    with qtbot.waitSignal(editor.music_changed, timeout=100):
        editor.redo()

    assert editor.music == 3
    assert editor.state.music == 3


def test_music_redo_state_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    editor.music = 3
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.music == 3
    assert editor.state.music == 3


def test_time_update_time_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)

    with qtbot.waitSignal(editor.time_changed, timeout=100):
        editor.time = 3

    assert editor.time == 3
    assert editor.state.time == 3


def test_time_update_state_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.time = 3

    assert editor.time == 3
    assert editor.state.time == 3


def test_time_undo_time_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    expected = editor.time
    editor.time = 3

    with qtbot.waitSignal(editor.time_changed, timeout=100):
        editor.undo()

    assert editor.time == expected
    assert editor.state.time == expected


def test_time_undo_state_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    expected = editor.time
    editor.time = 3

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.time == expected
    assert editor.state.time == expected


def test_time_redo_time_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    editor.time = 3
    editor.undo()

    with qtbot.waitSignal(editor.time_changed, timeout=100):
        editor.redo()

    assert editor.time == 3
    assert editor.state.time == 3


def test_time_redo_state_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    editor.time = 3
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.time == 3
    assert editor.state.time == 3


def test_scroll_update_scroll_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)

    with qtbot.waitSignal(editor.scroll_changed, timeout=100):
        editor.scroll = 2

    assert editor.scroll == 2
    assert editor.state.scroll == 2


def test_scroll_update_state_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.scroll = 2

    assert editor.scroll == 2
    assert editor.state.scroll == 2


def test_scroll_undo_scroll_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    expected = editor.scroll
    editor.scroll = 2

    with qtbot.waitSignal(editor.scroll_changed, timeout=100):
        editor.undo()

    assert editor.scroll == expected
    assert editor.state.scroll == expected


def test_scroll_undo_state_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    expected = editor.scroll
    editor.scroll = 2

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.scroll == expected
    assert editor.state.scroll == expected


def test_scroll_redo_scroll_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    editor.scroll = 2
    editor.undo()

    with qtbot.waitSignal(editor.scroll_changed, timeout=100):
        editor.redo()

    assert editor.scroll == 2
    assert editor.state.scroll == 2


def test_scroll_redo_state_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    editor.scroll = 2
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.scroll == 2
    assert editor.state.scroll == 2


def test_horizontal_update_horizontal_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)

    with qtbot.waitSignal(editor.horizontal_changed, timeout=100):
        editor.horizontal = False

    assert not editor.horizontal
    assert not editor.state.horizontal


def test_horizontal_update_state_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.horizontal = False

    assert not editor.horizontal
    assert not editor.state.horizontal


def test_horizontal_undo_horizontal_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    expected = editor.horizontal
    editor.horizontal = False

    with qtbot.waitSignal(editor.horizontal_changed, timeout=100):
        editor.undo()

    assert editor.horizontal == expected
    assert editor.state.horizontal == expected


def test_horizontal_undo_state_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    expected = editor.horizontal
    editor.horizontal = False

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.horizontal == expected
    assert editor.state.horizontal == expected


def test_horizontal_redo_horizontal_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    editor.horizontal = False
    editor.undo()

    with qtbot.waitSignal(editor.horizontal_changed, timeout=100):
        editor.redo()

    assert not editor.horizontal
    assert not editor.state.horizontal


def test_horizontal_redo_state_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    editor.horizontal = False
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert not editor.horizontal
    assert not editor.state.horizontal


def test_pipe_ends_level_update_pipe_ends_level_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)

    with qtbot.waitSignal(editor.pipe_ends_level_changed, timeout=100):
        editor.pipe_ends_level = True

    assert editor.pipe_ends_level
    assert editor.state.pipe_ends_level


def test_pipe_ends_level_update_state_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.pipe_ends_level = True

    assert editor.pipe_ends_level
    assert editor.state.pipe_ends_level


def test_pipe_ends_level_undo_pipe_ends_level_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    expected = editor.pipe_ends_level
    editor.pipe_ends_level = True

    with qtbot.waitSignal(editor.pipe_ends_level_changed, timeout=100):
        editor.undo()

    assert editor.pipe_ends_level == expected
    assert editor.state.pipe_ends_level == expected


def test_pipe_ends_level_undo_state_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    expected = editor.pipe_ends_level
    editor.pipe_ends_level = True

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.pipe_ends_level == expected
    assert editor.state.pipe_ends_level == expected


def test_pipe_ends_level_redo_pipe_ends_level_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    editor.pipe_ends_level = True
    editor.undo()

    with qtbot.waitSignal(editor.pipe_ends_level_changed, timeout=100):
        editor.redo()

    assert editor.pipe_ends_level
    assert editor.state.pipe_ends_level


def test_pipe_ends_level_redo_state_changed(qtbot, level_data):
    editor = LevelDataEditor(None, level_data)
    editor.pipe_ends_level = True
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.pipe_ends_level
    assert editor.state.pipe_ends_level


def test_display_initialization(qtbot):
    LevelDataDisplay(None, 0, 1, 2, 3, True, False)


def test_display_equality(qtbot):
    assert LevelDataDisplay(None, 0, 1, 2, 3, True, False) == LevelDataDisplay(None, 0, 1, 2, 3, True, False)


def test_display_inequality(qtbot):
    assert LevelDataDisplay(None, 0, 1, 2, 3, True, False) != LevelDataDisplay(None, 3, 2, 1, 0, False, True)


def test_display_other_inequality(qtbot):
    assert LevelDataDisplay(None, 0, 1, 2, 3, True, False) != 3


def test_display_get_level_length(qtbot):
    display = LevelDataDisplay(None, 0, 1, 2, 3, True, False)
    assert 0 == display.level_length


def test_display_set_level_length(qtbot, data_display: LevelDataDisplay):
    data_display.level_length = 3
    assert 3 == data_display.level_length


def test_display_get_music(qtbot):
    display = LevelDataDisplay(None, 0, 1, 2, 3, True, False)
    assert 1 == display.music


def test_display_set_music(qtbot, data_display: LevelDataDisplay):
    data_display.music = 3
    assert 3 == data_display.music


def test_display_get_etime(qtbot):
    display = LevelDataDisplay(None, 0, 1, 2, 3, True, False)
    assert 2 == display.time


def test_display_set_time(qtbot, data_display: LevelDataDisplay):
    data_display.time = 3
    assert 3 == data_display.time


def test_display_set_scroll(qtbot, data_display: LevelDataDisplay):
    data_display.scroll = 1
    assert 1 == data_display.scroll


def test_display_set_horizontal(qtbot, data_display: LevelDataDisplay):
    data_display.horizontal = False
    assert not data_display.horizontal


def test_display_set_pipe_ends_level(qtbot, data_display: LevelDataDisplay):
    data_display.pipe_ends_level = True
    assert data_display.pipe_ends_level


def test_set_level_length(qtbot, data_editor: LevelDataEditor):
    data_editor._display.level_length = 3
    assert 3 == data_editor.level_length


def test_set_music(qtbot, data_editor: LevelDataEditor):
    data_editor._display.music = 3
    assert 3 == data_editor.music


def test_set_time(qtbot, data_editor: LevelDataEditor):
    data_editor._display.time = 3
    assert 3 == data_editor.time


def test_set_scroll(qtbot, data_editor: LevelDataEditor):
    data_editor._display.scroll = 1
    assert 1 == data_editor.scroll


def test_set_horizontal(qtbot, data_editor: LevelDataEditor):
    data_editor._display.horizontal = False
    assert not data_editor.horizontal


def test_set_pipe_ends_level(qtbot, data_editor: LevelDataEditor):
    data_editor._display.pipe_ends_level = True
    assert data_editor.pipe_ends_level


def test_set_level_length_value(qtbot, data_editor: LevelDataEditor):
    data_editor._display.level_length_editor.setCurrentIndex(3)
    assert 3 == data_editor.level_length


def test_set_music_value(qtbot, data_editor: LevelDataEditor):
    data_editor._display.music_editor.setCurrentIndex(3)
    assert 3 == data_editor.music


def test_set_time_value(qtbot, data_editor: LevelDataEditor):
    data_editor._display.time_editor.setCurrentIndex(3)
    assert 3 == data_editor.time


def test_set_scroll_value(qtbot, data_editor: LevelDataEditor):
    data_editor._display.scroll_editor.setCurrentIndex(1)
    assert 1 == data_editor.scroll


def test_set_horizontal_value(qtbot, data_editor: LevelDataEditor):
    data_editor._display.horizontal_editor.setChecked(False)
    assert not data_editor.horizontal


def test_set_pipe_ends_level_value(qtbot, data_editor: LevelDataEditor):
    data_editor._display.pipe_ends_level_editor.setChecked(True)
    assert data_editor.pipe_ends_level
