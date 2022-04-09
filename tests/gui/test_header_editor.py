from hypothesis import given
from hypothesis.strategies import booleans, builds, integers, lists, text
from PySide6.QtWidgets import QMainWindow
from pytest import fixture

from foundry.game.level.util import DisplayInformation
from foundry.game.level.util import Level as LevelInformationState
from foundry.game.level.util import Location
from foundry.gui.HeaderEditor import (
    HeaderDisplay,
    HeaderEditor,
    HeaderState,
    header_state_to_level_header,
)
from foundry.gui.LevelDataEditor import LevelDataState
from foundry.gui.LevelGraphicsEditor import LevelGraphicsState
from foundry.gui.LevelStartEditor import LevelStartState
from foundry.gui.LevelWarpEditor import LevelWarpState
from foundry.gui.settings import FileSettings


def level_data_states():
    return builds(
        LevelDataState, integers(0, 15), integers(0, 63), integers(0, 3), integers(0, 3), booleans(), booleans()
    )


def level_start_states():
    return builds(LevelStartState, integers(0, 3), integers(0, 7), integers(0, 7))


def level_graphics_states():
    return builds(LevelGraphicsState, integers(0, 7), integers(0, 3), integers(0, 31))


def level_warp_states():
    return builds(LevelWarpState, integers(0, 0xFFFF), integers(0, 0xFFFF), integers(0, 15))


def level_locations():
    return builds(Location, integers(0, 8), integers(0))


def display_info():
    return builds(DisplayInformation, text(), text(), lists(level_locations()))


def level_info_states():
    return builds(
        LevelInformationState,
        display_info(),
        integers(0, 0xFFFF),
        integers(0, 0xFFFF),
        integers(0, 15),
        integers(0),
        integers(0),
    )


def header_states():
    return builds(
        HeaderState,
        level_data_states(),
        level_start_states(),
        level_graphics_states(),
        level_warp_states(),
        level_info_states(),
    )


@fixture
def header_state() -> HeaderState:
    return HeaderState(
        LevelDataState(0xE, 0, 1, 2, True, False),
        LevelStartState(0, 1, 2),
        LevelGraphicsState(7, 3, 4),
        LevelWarpState(0xFFFF, 0xEEEE, 1),
        LevelInformationState(DisplayInformation("name", "desc", []), 0xDDDD, 0xCCCC, 2, 100, 30),
    )


@fixture
def header_state_other() -> HeaderState:
    return HeaderState(
        LevelDataState(0, 0, 0, 0, False, True),
        LevelStartState(2, 1, 0),
        LevelGraphicsState(0, 0, 0),
        LevelWarpState(0xEEEE, 0xFFFF, 0),
        LevelInformationState(DisplayInformation("other name", "other desc", []), 0xCCCC, 0xDDDD, 0, 50, 15),
    )


@fixture
def level_bytes() -> bytearray:
    return bytearray([0, 1, 2, 3, 4, 5, 6, 7, 8])


@fixture
def empty_file_settings() -> FileSettings:
    return FileSettings(levels=[])


@fixture(scope="session")
def temp_app():
    yield QMainWindow()


@fixture
def header_display(temp_app, level_bytes: bytearray, empty_file_settings: FileSettings) -> HeaderDisplay:
    return HeaderDisplay(
        temp_app,
        LevelDataState(0xE, 0, 1, 2, True, False),
        LevelStartState(0, 1, 2),
        LevelGraphicsState(7, 3, 4),
        LevelWarpState(0xFFFF, 0xEEEE, 1),
        LevelInformationState(DisplayInformation("name", "desc", []), 0xDDDD, 0xCCCC, 2, 100, 30),
        level_bytes,
        empty_file_settings,
    )


@fixture
def header_editor(header_state: HeaderState, empty_file_settings: FileSettings) -> HeaderEditor:
    return HeaderEditor(None, header_state, empty_file_settings)


def test_header_state_initialization():
    HeaderState(
        LevelDataState(0xE, 0, 1, 2, True, False),
        LevelStartState(0, 1, 2),
        LevelGraphicsState(7, 3, 4),
        LevelWarpState(0xFFFF, 0xEEEE, 1),
        LevelInformationState(DisplayInformation("name", "desc", []), 0xDDDD, 0xCCCC, 2, 100, 30),
    )


def test_header_state_equality():
    assert HeaderState(
        LevelDataState(0xE, 0, 1, 2, True, False),
        LevelStartState(0, 1, 2),
        LevelGraphicsState(7, 3, 4),
        LevelWarpState(0xFFFF, 0xEEEE, 1),
        LevelInformationState(DisplayInformation("name", "desc", []), 0xDDDD, 0xCCCC, 2, 100, 30),
    ) == HeaderState(
        LevelDataState(0xE, 0, 1, 2, True, False),
        LevelStartState(0, 1, 2),
        LevelGraphicsState(7, 3, 4),
        LevelWarpState(0xFFFF, 0xEEEE, 1),
        LevelInformationState(DisplayInformation("name", "desc", []), 0xDDDD, 0xCCCC, 2, 100, 30),
    )


def test_header_state_inequality(header_state: HeaderState, header_state_other: HeaderState):
    assert header_state != header_state_other


def test_header_state_inequality_other(header_state: HeaderState):
    assert header_state != 1


def test_initialization(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    HeaderEditor(None, header_state, empty_file_settings)


def test_normal_equality(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    assert HeaderEditor(None, header_state, empty_file_settings) == HeaderEditor(
        None, header_state, empty_file_settings
    )


def test_normal_inequality(
    qtbot, header_state: HeaderState, header_state_other: HeaderState, empty_file_settings: FileSettings
):  # sourcery skip: de-morgan
    assert HeaderEditor(None, header_state, empty_file_settings) != HeaderEditor(
        None, header_state_other, empty_file_settings
    )


def test_equality_undo(
    qtbot, header_state: HeaderState, header_state_other: HeaderState, empty_file_settings: FileSettings
):
    editor1 = HeaderEditor(None, header_state, empty_file_settings)
    editor2 = HeaderEditor(None, header_state, empty_file_settings)
    editor1.state = header_state_other
    editor1.undo()
    assert editor1 != editor2

    editor2.state = header_state_other

    assert editor1 != editor2

    editor2.undo()
    assert editor1 == editor2


def test_equality_redo(
    qtbot, header_state: HeaderState, header_state_other: HeaderState, empty_file_settings: FileSettings
):
    editor1 = HeaderEditor(None, header_state, empty_file_settings)
    editor2 = HeaderEditor(None, header_state, empty_file_settings)
    editor1.state = header_state_other
    editor1.undo()
    editor1.redo()
    assert editor1 != editor2

    editor2.state = header_state_other

    assert editor1 == editor2

    editor2.undo()
    editor2.redo()
    assert editor1 == editor2


def test_inequality_other(qtbot, header_editor: HeaderEditor):
    assert header_editor != 5


def test_current_page_initialization(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    assert 0 == editor.current_page


def test_current_page_get_set(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.current_page = 1
    assert 1 == editor.current_page


def test_level_length_update_level_length_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.level_length_changed, timeout=100):
        editor.level_length = 3

    assert editor.level_length == 3
    assert editor.state.data.level_length == 3


def test_level_length_update_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.level_length = 3

    assert editor.level_length == 3
    assert editor.state.data.level_length == 3


def test_level_length_undo_level_length_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.level_length
    editor.level_length = 3

    with qtbot.waitSignal(editor.level_length_changed, timeout=100):
        editor.undo()

    assert editor.level_length == expected
    assert editor.state.data.level_length == expected


def test_level_length_undo_level_length_state_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.level_length
    editor.level_length = 3

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.level_length == expected
    assert editor.state.data.level_length == expected


def test_level_length_redo_level_length_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.level_length = 3
    editor.undo()

    with qtbot.waitSignal(editor.level_length_changed, timeout=100):
        editor.redo()

    assert editor.level_length == 3
    assert editor.state.data.level_length == 3


def test_level_length_redo_level_length_state_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.level_length = 3
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.level_length == 3
    assert editor.state.data.level_length == 3


def test_music_update_music_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.music_changed, timeout=100):
        editor.music = 3

    assert editor.music == 3
    assert editor.state.data.music == 3


def test_music_update_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.music = 3

    assert editor.music == 3
    assert editor.state.data.music == 3


def test_music_undo_music_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.music
    editor.music = 3

    with qtbot.waitSignal(editor.music_changed, timeout=100):
        editor.undo()

    assert editor.music == expected
    assert editor.state.data.music == expected


def test_music_undo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.music
    editor.music = 3

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.music == expected
    assert editor.state.data.music == expected


def test_music_redo_music_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.music = 3
    editor.undo()

    with qtbot.waitSignal(editor.music_changed, timeout=100):
        editor.redo()

    assert editor.music == 3
    assert editor.state.data.music == 3


def test_music_redo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.music = 3
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.music == 3
    assert editor.state.data.music == 3


def test_time_update_time_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.time_changed, timeout=100):
        editor.time = 3

    assert editor.time == 3
    assert editor.state.data.time == 3


def test_time_update_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.time = 3

    assert editor.time == 3
    assert editor.state.data.time == 3


def test_time_undo_time_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.time
    editor.time = 3

    with qtbot.waitSignal(editor.time_changed, timeout=100):
        editor.undo()

    assert editor.time == expected
    assert editor.state.data.time == expected


def test_time_undo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.time
    editor.time = 3

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.time == expected
    assert editor.state.data.time == expected


def test_time_redo_time_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.time = 3
    editor.undo()

    with qtbot.waitSignal(editor.time_changed, timeout=100):
        editor.redo()

    assert editor.time == 3
    assert editor.state.data.time == 3


def test_time_redo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.time = 3
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.time == 3
    assert editor.state.data.time == 3


def test_scroll_update_scroll_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.scroll_changed, timeout=100):
        editor.scroll = 3

    assert editor.scroll == 3
    assert editor.state.data.scroll == 3


def test_scroll_update_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.scroll = 3

    assert editor.scroll == 3
    assert editor.state.data.scroll == 3


def test_scroll_undo_scroll_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.scroll
    editor.scroll = 3

    with qtbot.waitSignal(editor.scroll_changed, timeout=100):
        editor.undo()

    assert editor.scroll == expected
    assert editor.state.data.scroll == expected


def test_scroll_undo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.scroll
    editor.scroll = 3

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.scroll == expected
    assert editor.state.data.scroll == expected


def test_scroll_redo_scroll_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.scroll = 3
    editor.undo()

    with qtbot.waitSignal(editor.scroll_changed, timeout=100):
        editor.redo()

    assert editor.scroll == 3
    assert editor.state.data.scroll == 3


def test_scroll_redo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.scroll = 3
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.scroll == 3
    assert editor.state.data.scroll == 3


def test_horizontal_update_horizontal_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.horizontal_changed, timeout=100):
        editor.horizontal = False

    assert not editor.horizontal
    assert not editor.state.data.horizontal


def test_horizontal_update_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.horizontal = False

    assert not editor.horizontal
    assert not editor.state.data.horizontal


def test_horizontal_undo_horizontal_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.horizontal
    editor.horizontal = False

    with qtbot.waitSignal(editor.horizontal_changed, timeout=100):
        editor.undo()

    assert editor.horizontal == expected
    assert editor.state.data.horizontal == expected


def test_horizontal_undo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.horizontal
    editor.horizontal = False

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.horizontal == expected
    assert editor.state.data.horizontal == expected


def test_horizontal_redo_horizontal_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.horizontal = False
    editor.undo()

    with qtbot.waitSignal(editor.horizontal_changed, timeout=100):
        editor.redo()

    assert not editor.horizontal
    assert not editor.state.data.horizontal


def test_horizontal_redo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.horizontal = False
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert not editor.horizontal
    assert not editor.state.data.horizontal


def test_pipe_ends_level_update_pipe_ends_level_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.pipe_ends_level_changed, timeout=100):
        editor.pipe_ends_level = True

    assert editor.pipe_ends_level
    assert editor.state.data.pipe_ends_level


def test_pipe_ends_level_update_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.pipe_ends_level = True

    assert editor.pipe_ends_level
    assert editor.state.data.pipe_ends_level


def test_pipe_ends_level_undo_pipe_ends_level_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.pipe_ends_level
    editor.pipe_ends_level = True

    with qtbot.waitSignal(editor.pipe_ends_level_changed, timeout=100):
        editor.undo()

    assert editor.pipe_ends_level == expected
    assert editor.state.data.pipe_ends_level == expected


def test_pipe_ends_level_undo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.pipe_ends_level
    editor.pipe_ends_level = True

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.pipe_ends_level == expected
    assert editor.state.data.pipe_ends_level == expected


def test_pipe_ends_level_redo_pipe_ends_level_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.pipe_ends_level = True
    editor.undo()

    with qtbot.waitSignal(editor.pipe_ends_level_changed, timeout=100):
        editor.redo()

    assert editor.pipe_ends_level
    assert editor.state.data.pipe_ends_level


def test_pipe_ends_level_redo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.pipe_ends_level = True
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.pipe_ends_level
    assert editor.state.data.pipe_ends_level


def test_x_position_update_x_position_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.x_position_changed, timeout=100):
        editor.x_position = 3

    assert editor.x_position == 3
    assert editor.state.start.x_position == 3


def test_x_position_update_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.x_position = 3

    assert editor.x_position == 3
    assert editor.state.start.x_position == 3


def test_x_position_undo_x_position_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.x_position
    editor.x_position = 3

    with qtbot.waitSignal(editor.x_position_changed, timeout=100):
        editor.undo()

    assert editor.x_position == expected
    assert editor.state.start.x_position == expected


def test_x_position_undo_x_position_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.x_position
    editor.x_position = 3

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.x_position == expected
    assert editor.state.start.x_position == expected


def test_x_position_redo_x_position_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.x_position = 3
    editor.undo()

    with qtbot.waitSignal(editor.x_position_changed, timeout=100):
        editor.redo()

    assert editor.x_position == 3
    assert editor.state.start.x_position == 3


def test_x_position_redo_x_position_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.x_position = 3
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.x_position == 3
    assert editor.state.start.x_position == 3


def test_y_position_update_y_position_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.y_position_changed, timeout=100):
        editor.y_position = 3

    assert editor.y_position == 3
    assert editor.state.start.y_position == 3


def test_y_position_update_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.y_position = 3

    assert editor.y_position == 3
    assert editor.state.start.y_position == 3


def test_y_position_undo_y_position_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.y_position
    editor.y_position = 3

    with qtbot.waitSignal(editor.y_position_changed, timeout=100):
        editor.undo()

    assert editor.y_position == expected
    assert editor.state.start.y_position == expected


def test_y_position_undo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.y_position
    editor.y_position = 3

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.y_position == expected
    assert editor.state.start.y_position == expected


def test_y_position_redo_y_position_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.y_position = 3
    editor.undo()

    with qtbot.waitSignal(editor.y_position_changed, timeout=100):
        editor.redo()

    assert editor.y_position == 3
    assert editor.state.start.y_position == 3


def test_y_position_redo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.y_position = 3
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.y_position == 3
    assert editor.state.start.y_position == 3


def test_action_update_action_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.action_changed, timeout=100):
        editor.action = 3

    assert editor.action == 3
    assert editor.state.start.action == 3


def test_action_update_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.action = 3

    assert editor.action == 3
    assert editor.state.start.action == 3


def test_action_undo_action_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.action
    editor.action = 3

    with qtbot.waitSignal(editor.action_changed, timeout=100):
        editor.undo()

    assert editor.action == expected
    assert editor.state.start.action == expected


def test_action_undo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.action
    editor.action = 3

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.action == expected
    assert editor.state.start.action == expected


def test_action_redo_action_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.action = 7
    editor.undo()

    with qtbot.waitSignal(editor.action_changed, timeout=100):
        editor.redo()

    assert editor.action == 7
    assert editor.state.start.action == 7


def test_action_redo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.action = 7
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.action == 7
    assert editor.state.start.action == 7


def test_generator_palette_update_generator_palette_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.generator_palette_changed, timeout=100):
        editor.generator_palette = 6

    assert editor.generator_palette == 6
    assert editor.state.graphics.generator_palette == 6


def test_generator_palette_update_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.generator_palette = 6

    assert editor.generator_palette == 6
    assert editor.state.graphics.generator_palette == 6


def test_generator_palette_undo_generator_palette_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.generator_palette
    editor.generator_palette = 3

    with qtbot.waitSignal(editor.generator_palette_changed, timeout=100):
        editor.undo()

    assert editor.generator_palette == expected
    assert editor.state.graphics.generator_palette == expected


def test_generator_palette_undo_generator_palette_state_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.generator_palette
    editor.generator_palette = 6

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.generator_palette == expected
    assert editor.state.graphics.generator_palette == expected


def test_generator_palette_redo_generator_palette_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.generator_palette = 6
    editor.undo()

    with qtbot.waitSignal(editor.generator_palette_changed, timeout=100):
        editor.redo()

    assert editor.generator_palette == 6
    assert editor.state.graphics.generator_palette == 6


def test_generator_palette_redo_generator_palette_state_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.generator_palette = 6
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.generator_palette == 6
    assert editor.state.graphics.generator_palette == 6


def test_enemy_palette_update_enemy_palette_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.enemy_palette_changed, timeout=100):
        editor.enemy_palette = 2

    assert editor.enemy_palette == 2
    assert editor.state.graphics.enemy_palette == 2


def test_enemy_palette_update_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.enemy_palette = 2

    assert editor.enemy_palette == 2
    assert editor.state.graphics.enemy_palette == 2


def test_enemy_palette_undo_enemy_palette_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.enemy_palette
    editor.enemy_palette = 2

    with qtbot.waitSignal(editor.enemy_palette_changed, timeout=100):
        editor.undo()

    assert editor.enemy_palette == expected
    assert editor.state.graphics.enemy_palette == expected


def test_enemy_palette_undo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.enemy_palette
    editor.enemy_palette = 2

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.enemy_palette == expected
    assert editor.state.graphics.enemy_palette == expected


def test_enemy_palette_redo_enemy_palette_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.enemy_palette = 2
    editor.undo()

    with qtbot.waitSignal(editor.enemy_palette_changed, timeout=100):
        editor.redo()

    assert editor.enemy_palette == 2
    assert editor.state.graphics.enemy_palette == 2


def test_enemy_palette_redo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.enemy_palette = 2
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.enemy_palette == 2
    assert editor.state.graphics.enemy_palette == 2


def test_graphics_set_update_graphics_set_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.graphics_set_changed, timeout=100):
        editor.graphics_set = 10

    assert editor.graphics_set == 10
    assert editor.state.graphics.graphics_set == 10


def test_graphics_set_update_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.graphics_set = 10

    assert editor.graphics_set == 10
    assert editor.state.graphics.graphics_set == 10


def test_graphics_set_undo_graphics_set_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.graphics_set
    editor.graphics_set = 10

    with qtbot.waitSignal(editor.graphics_set_changed, timeout=100):
        editor.undo()

    assert editor.graphics_set == expected
    assert editor.state.graphics.graphics_set == expected


def test_graphics_set_undo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.graphics_set
    editor.graphics_set = 10

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.graphics_set == expected
    assert editor.state.graphics.graphics_set == expected


def test_graphics_set_redo_graphics_set_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.graphics_set = 10
    editor.undo()

    with qtbot.waitSignal(editor.graphics_set_changed, timeout=100):
        editor.redo()

    assert editor.graphics_set == 10
    assert editor.state.graphics.graphics_set == 10


def test_graphics_set_redo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.graphics_set = 10
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.graphics_set == 10
    assert editor.state.graphics.graphics_set == 10


def test_next_level_generator_pointer_update_next_level_generator_pointer_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.next_level_generator_pointer_changed, timeout=100):
        editor.next_level_generator_pointer = 10

    assert editor.next_level_generator_pointer == 10
    assert editor.state.warp.generator_pointer == 10


def test_next_level_generator_pointer_update_state_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.next_level_generator_pointer = 10

    assert editor.next_level_generator_pointer == 10
    assert editor.state.warp.generator_pointer == 10


def test_next_level_generator_pointer_undo_next_level_generator_pointer_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.next_level_generator_pointer
    editor.next_level_generator_pointer = 10

    with qtbot.waitSignal(editor.next_level_generator_pointer_changed, timeout=100):
        editor.undo()

    assert editor.next_level_generator_pointer == expected
    assert editor.state.warp.generator_pointer == expected


def test_next_level_generator_pointer_undo_next_level_generator_pointer_state_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.next_level_generator_pointer
    editor.next_level_generator_pointer = 10

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.next_level_generator_pointer == expected
    assert editor.state.warp.generator_pointer == expected


def test_next_level_generator_pointer_redo_next_level_generator_pointer_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.next_level_generator_pointer = 10
    editor.undo()

    with qtbot.waitSignal(editor.next_level_generator_pointer_changed, timeout=100):
        editor.redo()

    assert editor.next_level_generator_pointer == 10
    assert editor.state.warp.generator_pointer == 10


def test_next_level_generator_pointer_redo_next_level_generator_pointer_state_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.next_level_generator_pointer = 10
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.next_level_generator_pointer == 10
    assert editor.state.warp.generator_pointer == 10


def test_next_level_enemy_pointer_update_next_level_enemy_pointer_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.next_level_enemy_pointer_changed, timeout=100):
        editor.next_level_enemy_pointer = 10

    assert editor.next_level_enemy_pointer == 10
    assert editor.state.warp.enemy_pointer == 10


def test_next_level_enemy_pointer_update_state_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.next_level_enemy_pointer = 10

    assert editor.next_level_enemy_pointer == 10
    assert editor.state.warp.enemy_pointer == 10


def test_next_level_enemy_pointer_undo_next_level_enemy_pointer_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.next_level_enemy_pointer
    editor.next_level_enemy_pointer = 10

    with qtbot.waitSignal(editor.next_level_enemy_pointer_changed, timeout=100):
        editor.undo()

    assert editor.next_level_enemy_pointer == expected
    assert editor.state.warp.enemy_pointer == expected


def test_next_level_enemy_pointer_undo_state_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.next_level_enemy_pointer
    editor.next_level_enemy_pointer = 10

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.next_level_enemy_pointer == expected
    assert editor.state.warp.enemy_pointer == expected


def test_next_level_enemy_pointer_redo_next_level_enemy_pointer_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.next_level_enemy_pointer = 10
    editor.undo()

    with qtbot.waitSignal(editor.next_level_enemy_pointer_changed, timeout=100):
        editor.redo()

    assert editor.next_level_enemy_pointer == 10
    assert editor.state.warp.enemy_pointer == 10


def test_next_level_enemy_pointer_redo_state_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.next_level_enemy_pointer = 10
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.next_level_enemy_pointer == 10
    assert editor.state.warp.enemy_pointer == 10


def test_next_level_tileset_update_next_level_tileset_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.next_level_tileset_changed, timeout=100):
        editor.next_level_tileset = 10

    assert editor.next_level_tileset == 10
    assert editor.state.warp.tileset == 10


def test_next_level_tileset_update_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.next_level_tileset = 10

    assert editor.next_level_tileset == 10
    assert editor.state.warp.tileset == 10


def test_next_level_tileset_undo_next_level_tileset_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.next_level_tileset
    editor.next_level_tileset = 10

    with qtbot.waitSignal(editor.next_level_tileset_changed, timeout=100):
        editor.undo()

    assert editor.next_level_tileset == expected
    assert editor.state.warp.tileset == expected


def test_next_level_tileset_undo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.next_level_tileset
    editor.next_level_tileset = 10

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.next_level_tileset == expected
    assert editor.state.warp.tileset == expected


def test_next_level_tileset_redo_next_level_tileset_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.next_level_tileset = 10
    editor.undo()

    with qtbot.waitSignal(editor.next_level_tileset_changed, timeout=100):
        editor.redo()

    assert editor.next_level_tileset == 10
    assert editor.state.warp.tileset == 10


def test_next_level_tileset_redo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.next_level_tileset = 10
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.next_level_tileset == 10
    assert editor.state.warp.tileset == 10


def test_name_updates_name(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.name = "new name"
    assert editor.name == "new name"
    assert editor.state.info.display_information.name == "new name"


def test_name_update_name_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.name_changed, timeout=100):
        editor.name = "new name"

    assert editor.name == "new name"
    assert editor.state.info.display_information.name == "new name"


def test_name_update_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.name = "new name"

    assert editor.name == "new name"
    assert editor.state.info.display_information.name == "new name"


def test_name_undo_name_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.name = "new name"

    with qtbot.waitSignal(editor.name_changed, timeout=100):
        editor.undo()

    assert editor.name == "name"
    assert editor.state.info.display_information.name == "name"


def test_name_undo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.name = "new name"

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.name == "name"
    assert editor.state.info.display_information.name == "name"


def test_name_redo_name_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.name = "new name"
    editor.undo()

    with qtbot.waitSignal(editor.name_changed, timeout=100):
        editor.redo()

    assert editor.name == "new name"
    assert editor.state.info.display_information.name == "new name"


def test_name_redo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.name = "new name"
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.name == "new name"
    assert editor.state.info.display_information.name == "new name"


def test_description_update_description_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.description_changed, timeout=100):
        editor.description = "new description"

    assert editor.description == "new description"
    assert editor.state.info.display_information.description == "new description"


def test_description_update_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.description = "new description"

    assert editor.description == "new description"
    assert editor.state.info.display_information.description == "new description"


def test_description_undo_description_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.description
    editor.description = "new description"

    with qtbot.waitSignal(editor.description_changed, timeout=100):
        editor.undo()

    assert editor.description == expected
    assert editor.state.info.display_information.description == expected


def test_description_undo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.description
    editor.description = "new description"

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.description == expected
    assert editor.state.info.display_information.description == expected


def test_description_redo_description_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.description = "new description"
    editor.undo()

    with qtbot.waitSignal(editor.description_changed, timeout=100):
        editor.redo()

    assert editor.description == "new description"
    assert editor.state.info.display_information.description == "new description"


def test_description_redo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.description = "new description"
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.description == "new description"
    assert editor.state.info.display_information.description == "new description"


def test_generator_space_update_generator_space_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.generator_space_changed, timeout=100):
        editor.generator_space = 10

    assert editor.generator_space == 10
    assert editor.state.info.generator_size == 10


def test_generator_space_update_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.generator_space = 10

    assert editor.generator_space == 10
    assert editor.state.info.generator_size == 10


def test_generator_space_undo_generator_space_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.generator_space
    editor.generator_space = 10

    with qtbot.waitSignal(editor.generator_space_changed, timeout=100):
        editor.undo()

    assert editor.generator_space == expected
    assert editor.state.info.generator_size == expected


def test_generator_space_undo_generator_space_state_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.generator_space
    editor.generator_space = 10

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.generator_space == expected
    assert editor.state.info.generator_size == expected


def test_generator_space_redo_generator_space_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.generator_space = 10
    editor.undo()

    with qtbot.waitSignal(editor.generator_space_changed, timeout=100):
        editor.redo()

    assert editor.generator_space == 10
    assert editor.state.info.generator_size == 10


def test_generator_space_redo_generator_space_state_changed(
    qtbot, header_state: HeaderState, empty_file_settings: FileSettings
):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.generator_space = 10
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.generator_space == 10
    assert editor.state.info.generator_size == 10


def test_enemy_space_update_enemy_space_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.enemy_space_changed, timeout=100):
        editor.enemy_space = 10

    assert editor.enemy_space == 10
    assert editor.state.info.enemy_size == 10


def test_enemy_space_update_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.enemy_space = 10

    assert editor.enemy_space == 10
    assert editor.state.info.enemy_size == 10


def test_enemy_space_undo_enemy_space_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.enemy_space
    editor.enemy_space = 10

    with qtbot.waitSignal(editor.enemy_space_changed, timeout=100):
        editor.undo()

    assert editor.enemy_space == expected
    assert editor.state.info.enemy_size == expected


def test_enemy_space_undo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    expected = editor.enemy_space
    editor.enemy_space = 10

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.enemy_space == expected
    assert editor.state.info.enemy_size == expected


def test_enemy_space_redo_enemy_space_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.enemy_space = 10
    editor.undo()

    with qtbot.waitSignal(editor.enemy_space_changed, timeout=100):
        editor.redo()

    assert editor.enemy_space == 10
    assert editor.state.info.enemy_size == 10


def test_enemy_space_redo_state_changed(qtbot, header_state: HeaderState, empty_file_settings: FileSettings):
    editor = HeaderEditor(None, header_state, empty_file_settings)
    editor.enemy_space = 10
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.enemy_space == 10
    assert editor.state.info.enemy_size == 10


def test_display_current_page_initialization(
    qtbot, temp_app, level_bytes: bytearray, empty_file_settings: FileSettings
):
    display = HeaderDisplay(
        temp_app,
        LevelDataState(0xE, 0, 1, 2, True, False),
        LevelStartState(0, 1, 2),
        LevelGraphicsState(7, 3, 4),
        LevelWarpState(0xFFFF, 0xEEEE, 1),
        LevelInformationState(DisplayInformation("name", "desc", []), 0xDDDD, 0xCCCC, 2, 100, 30),
        level_bytes,
        empty_file_settings,
    )
    assert 0 == display.current_page


def test_display_current_page_get_set(qtbot, header_display: HeaderDisplay):
    header_display.current_page = 1
    assert 1 == header_display.current_page


def test_display_get_data_state(qtbot, level_bytes: bytearray, empty_file_settings: FileSettings):
    display = HeaderDisplay(
        QMainWindow(),
        LevelDataState(0xE, 0, 1, 2, True, False),
        LevelStartState(0, 1, 2),
        LevelGraphicsState(7, 3, 4),
        LevelWarpState(0xFFFF, 0xEEEE, 1),
        LevelInformationState(DisplayInformation("name", "desc", []), 0xDDDD, 0xCCCC, 2, 100, 30),
        level_bytes,
        empty_file_settings,
    )
    assert LevelDataState(0xE, 0, 1, 2, True, False) == display.data


def test_display_set_data_state(qtbot, header_display: HeaderDisplay):
    header_display.data = LevelDataState(0xD, 2, 0, 1, False, True)
    assert LevelDataState(0xD, 2, 0, 1, False, True) == header_display.data


def test_display_get_start_state(qtbot, level_bytes: bytearray, empty_file_settings: FileSettings):
    display = HeaderDisplay(
        QMainWindow(),
        LevelDataState(0xE, 0, 1, 2, True, False),
        LevelStartState(0, 1, 2),
        LevelGraphicsState(7, 3, 4),
        LevelWarpState(0xFFFF, 0xEEEE, 1),
        LevelInformationState(DisplayInformation("name", "desc", []), 0xDDDD, 0xCCCC, 2, 100, 30),
        level_bytes,
        empty_file_settings,
    )
    assert LevelStartState(0, 1, 2) == display.start


def test_display_set_start_state(qtbot, header_display: HeaderDisplay):
    header_display.start = LevelStartState(2, 0, 1)
    assert LevelStartState(2, 0, 1) == header_display.start


def test_display_get_graphics_state(qtbot, level_bytes: bytearray, empty_file_settings: FileSettings):
    display = HeaderDisplay(
        QMainWindow(),
        LevelDataState(0xE, 0, 1, 2, True, False),
        LevelStartState(0, 1, 2),
        LevelGraphicsState(7, 3, 4),
        LevelWarpState(0xFFFF, 0xEEEE, 1),
        LevelInformationState(DisplayInformation("name", "desc", []), 0xDDDD, 0xCCCC, 2, 100, 30),
        level_bytes,
        empty_file_settings,
    )
    assert LevelGraphicsState(7, 3, 4) == display.graphics


def test_display_set_graphics_state(qtbot, header_display: HeaderDisplay):
    header_display.graphics = LevelGraphicsState(0, 1, 2)
    assert LevelGraphicsState(0, 1, 2) == header_display.graphics


def test_display_get_warp_state(qtbot, level_bytes: bytearray, empty_file_settings: FileSettings):
    display = HeaderDisplay(
        QMainWindow(),
        LevelDataState(0xE, 0, 1, 2, True, False),
        LevelStartState(0, 1, 2),
        LevelGraphicsState(7, 3, 4),
        LevelWarpState(0xFFFF, 0xEEEE, 1),
        LevelInformationState(DisplayInformation("name", "desc", []), 0xDDDD, 0xCCCC, 2, 100, 30),
        level_bytes,
        empty_file_settings,
    )
    assert LevelWarpState(0xFFFF, 0xEEEE, 1) == display.warp


def test_display_set_warp_state(qtbot, header_display: HeaderDisplay):
    header_display.warp = LevelWarpState(0xEEEE, 0xFFFF, 0)
    assert LevelWarpState(0xEEEE, 0xFFFF, 0) == header_display.warp


def test_display_get_level_info_state(qtbot, level_bytes: bytearray, empty_file_settings: FileSettings):
    display = HeaderDisplay(
        QMainWindow(),
        LevelDataState(0xE, 0, 1, 2, True, False),
        LevelStartState(0, 1, 2),
        LevelGraphicsState(7, 3, 4),
        LevelWarpState(0xFFFF, 0xEEEE, 1),
        LevelInformationState(DisplayInformation("name", "desc", []), 0xDDDD, 0xCCCC, 2, 100, 30),
        level_bytes,
        empty_file_settings,
    )
    assert LevelInformationState(DisplayInformation("name", "desc", []), 0xDDDD, 0xCCCC, 2, 100, 30) == display.info


def test_display_set_level_info_state(qtbot, header_display: HeaderDisplay):
    # Note that the pointers and tileset are not relevant for the info display.
    header_display.info = LevelInformationState(DisplayInformation("other", "stuff", []), 0xDDDD, 0xCCCC, 2, 50, 15)
    assert (
        LevelInformationState(DisplayInformation("other", "stuff", []), 0xDDDD, 0xCCCC, 2, 50, 15)
        == header_display.info
    )


@given(header_states())
def test_header_state_to_bytes(header_state: HeaderState):
    header_state_to_level_header(header_state)
