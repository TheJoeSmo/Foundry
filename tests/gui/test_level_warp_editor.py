from pytest import fixture

from foundry.gui.LevelWarpEditor import (
    LevelWarpDisplay,
    LevelWarpEditor,
    LevelWarpState,
)


@fixture
def warp_info() -> LevelWarpState:
    return LevelWarpState(0, 1, 2)


@fixture
def warp_display() -> LevelWarpDisplay:
    return LevelWarpDisplay(None, 0, 1, 2)


@fixture
def warp_editor(warp_info):
    return LevelWarpEditor(None, warp_info)


def test_warp_state_initialization():
    LevelWarpState(0, 1, 2)


def test_warp_state_equality():
    assert LevelWarpState(0, 1, 2) == LevelWarpState(0, 1, 2)


def test_warp_state_inequality():
    assert LevelWarpState(0, 1, 2) != LevelWarpState(2, 1, 0)


def test_warp_state_inequality_other():
    assert LevelWarpState(0, 1, 2) != 1


def test_initialization(qtbot, warp_info):
    LevelWarpEditor(None, warp_info)


def test_normal_equality(qtbot, warp_info):
    assert LevelWarpEditor(None, warp_info) == LevelWarpEditor(None, warp_info)


def test_normal_inequality(qtbot):  # sourcery skip: de-morgan
    assert LevelWarpEditor(None, LevelWarpState(0, 1, 2)) != LevelWarpEditor(None, LevelWarpState(2, 1, 0))


def test_equality_undo(qtbot, warp_info):
    editor1 = LevelWarpEditor(None, warp_info)
    editor2 = LevelWarpEditor(None, warp_info)
    editor1.state = LevelWarpState(2, 1, 0)
    editor1.undo()
    assert editor1 != editor2

    editor2.state = LevelWarpState(2, 1, 0)

    assert editor1 != editor2

    editor2.undo()
    assert editor1 == editor2


def test_equality_redo(qtbot, warp_info):
    editor1 = LevelWarpEditor(None, warp_info)
    editor2 = LevelWarpEditor(None, warp_info)
    editor1.state = LevelWarpState(2, 1, 0)
    editor1.undo()
    editor1.redo()
    assert editor1 != editor2

    editor2.state = LevelWarpState(2, 1, 0)

    assert editor1 == editor2

    editor2.undo()
    editor2.redo()
    assert editor1 == editor2


def test_inequality_other(qtbot, warp_editor):
    assert warp_editor != 5


def test_generator_pointer_update_generator_pointer_changed(qtbot, warp_info):
    editor = LevelWarpEditor(None, warp_info)

    with qtbot.waitSignal(editor.generator_pointer_changed, timeout=100):
        editor.generator_pointer = 10

    assert editor.generator_pointer == 10
    assert editor.state.generator_pointer == 10


def test_generator_pointer_update_state_changed(qtbot, warp_info):
    editor = LevelWarpEditor(None, warp_info)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.generator_pointer = 10

    assert editor.generator_pointer == 10
    assert editor.state.generator_pointer == 10


def test_generator_pointer_undo_generator_pointer_changed(qtbot, warp_info):
    editor = LevelWarpEditor(None, warp_info)
    expected = editor.generator_pointer
    editor.generator_pointer = 10

    with qtbot.waitSignal(editor.generator_pointer_changed, timeout=100):
        editor.undo()

    assert editor.generator_pointer == expected
    assert editor.state.generator_pointer == expected


def test_generator_pointer_undo_generator_pointer_state_changed(qtbot, warp_info):
    editor = LevelWarpEditor(None, warp_info)
    expected = editor.generator_pointer
    editor.generator_pointer = 10

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.generator_pointer == expected
    assert editor.state.generator_pointer == expected


def test_generator_pointer_redo_generator_pointer_changed(qtbot, warp_info):
    editor = LevelWarpEditor(None, warp_info)
    editor.generator_pointer = 10
    editor.undo()

    with qtbot.waitSignal(editor.generator_pointer_changed, timeout=100):
        editor.redo()

    assert editor.generator_pointer == 10
    assert editor.state.generator_pointer == 10


def test_generator_pointer_redo_generator_pointer_state_changed(qtbot, warp_info):
    editor = LevelWarpEditor(None, warp_info)
    editor.generator_pointer = 10
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.generator_pointer == 10
    assert editor.state.generator_pointer == 10


def test_enemy_pointer_update_enemy_pointer_changed(qtbot, warp_info):
    editor = LevelWarpEditor(None, warp_info)

    with qtbot.waitSignal(editor.enemy_pointer_changed, timeout=100):
        editor.enemy_pointer = 10

    assert editor.enemy_pointer == 10
    assert editor.state.enemy_pointer == 10


def test_enemy_pointer_update_state_changed(qtbot, warp_info):
    editor = LevelWarpEditor(None, warp_info)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.enemy_pointer = 10

    assert editor.enemy_pointer == 10
    assert editor.state.enemy_pointer == 10


def test_enemy_pointer_undo_enemy_pointer_changed(qtbot, warp_info):
    editor = LevelWarpEditor(None, warp_info)
    expected = editor.enemy_pointer
    editor.enemy_pointer = 10

    with qtbot.waitSignal(editor.enemy_pointer_changed, timeout=100):
        editor.undo()

    assert editor.enemy_pointer == expected
    assert editor.state.enemy_pointer == expected


def test_enemy_pointer_undo_state_changed(qtbot, warp_info):
    editor = LevelWarpEditor(None, warp_info)
    expected = editor.enemy_pointer
    editor.enemy_pointer = 10

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.enemy_pointer == expected
    assert editor.state.enemy_pointer == expected


def test_enemy_pointer_redo_enemy_pointer_changed(qtbot, warp_info):
    editor = LevelWarpEditor(None, warp_info)
    editor.enemy_pointer = 10
    editor.undo()

    with qtbot.waitSignal(editor.enemy_pointer_changed, timeout=100):
        editor.redo()

    assert editor.enemy_pointer == 10
    assert editor.state.enemy_pointer == 10


def test_enemy_pointer_redo_state_changed(qtbot, warp_info):
    editor = LevelWarpEditor(None, warp_info)
    editor.enemy_pointer = 10
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.enemy_pointer == 10
    assert editor.state.enemy_pointer == 10


def test_tileset_update_tileset_changed(qtbot, warp_info):
    editor = LevelWarpEditor(None, warp_info)

    with qtbot.waitSignal(editor.tileset_changed, timeout=100):
        editor.tileset = 10

    assert editor.tileset == 10
    assert editor.state.tileset == 10


def test_tileset_update_state_changed(qtbot, warp_info):
    editor = LevelWarpEditor(None, warp_info)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.tileset = 10

    assert editor.tileset == 10
    assert editor.state.tileset == 10


def test_tileset_undo_tileset_changed(qtbot, warp_info):
    editor = LevelWarpEditor(None, warp_info)
    expected = editor.tileset
    editor.tileset = 10

    with qtbot.waitSignal(editor.tileset_changed, timeout=100):
        editor.undo()

    assert editor.tileset == expected
    assert editor.state.tileset == expected


def test_tileset_undo_state_changed(qtbot, warp_info):
    editor = LevelWarpEditor(None, warp_info)
    expected = editor.tileset
    editor.tileset = 10

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.tileset == expected
    assert editor.state.tileset == expected


def test_tileset_redo_tileset_changed(qtbot, warp_info):
    editor = LevelWarpEditor(None, warp_info)
    editor.tileset = 10
    editor.undo()

    with qtbot.waitSignal(editor.tileset_changed, timeout=100):
        editor.redo()

    assert editor.tileset == 10
    assert editor.state.tileset == 10


def test_tileset_redo_state_changed(qtbot, warp_info):
    editor = LevelWarpEditor(None, warp_info)
    editor.tileset = 10
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.tileset == 10
    assert editor.state.tileset == 10


def test_display_initialization(qtbot):
    LevelWarpDisplay(None, 0, 1, 2)


def test_display_equality(qtbot):
    assert LevelWarpDisplay(None, 0, 1, 2) == LevelWarpDisplay(None, 0, 1, 2)


def test_display_inequality(qtbot):
    assert LevelWarpDisplay(None, 0, 1, 2) != LevelWarpDisplay(None, 2, 1, 0)


def test_display_other_inequality(qtbot):
    assert LevelWarpDisplay(None, 0, 1, 2) != 5


def test_display_get_generator_pointer(qtbot):
    display = LevelWarpDisplay(None, 0, 1, 2)
    assert 0 == display.generator_pointer


def test_display_set_generator_pointer(qtbot, warp_display: LevelWarpDisplay):
    warp_display.generator_pointer = 5
    assert 5 == warp_display.generator_pointer


def test_display_get_enemy_pointer(qtbot):
    display = LevelWarpDisplay(None, 0, 1, 2)
    assert 1 == display.enemy_pointer


def test_display_set_enemy_pointer(qtbot, warp_display: LevelWarpDisplay):
    warp_display.enemy_pointer = 5
    assert 5 == warp_display.enemy_pointer


def test_display_get_etileset(qtbot):
    display = LevelWarpDisplay(None, 0, 1, 2)
    assert 2 == display.tileset


def test_display_set_tileset(qtbot, warp_display: LevelWarpDisplay):
    warp_display.tileset = 5
    assert 5 == warp_display.tileset


def test_set_generator_pointer(qtbot, warp_editor: LevelWarpEditor):
    warp_editor._display.generator_pointer = 5
    assert 5 == warp_editor.generator_pointer


def test_set_enemy_pointer(qtbot, warp_editor: LevelWarpEditor):
    warp_editor._display.enemy_pointer = 5
    assert 5 == warp_editor.enemy_pointer


def test_set_tileset(qtbot, warp_editor: LevelWarpEditor):
    warp_editor._display.tileset = 5
    assert 5 == warp_editor.tileset


def test_set_generator_pointer_value(qtbot, warp_editor: LevelWarpEditor):
    warp_editor._display.generator_pointer_editor.setValue(5)
    assert 5 == warp_editor.generator_pointer


def test_set_enemy_pointer_value(qtbot, warp_editor: LevelWarpEditor):
    warp_editor._display.enemy_pointer_editor.setValue(5)
    assert 5 == warp_editor.enemy_pointer


def test_set_tileset_value(qtbot, warp_editor: LevelWarpEditor):
    warp_editor._display.tileset_editor.setCurrentIndex(5)
    assert 5 == warp_editor.tileset
