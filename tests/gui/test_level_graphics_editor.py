from pytest import fixture

from foundry.gui.LevelGraphicsEditor import (
    LevelGraphicsDisplay,
    LevelGraphicsEditor,
    LevelGraphicsState,
)


@fixture
def warp_info() -> LevelGraphicsState:
    return LevelGraphicsState(0, 1, 2)


@fixture
def warp_display() -> LevelGraphicsDisplay:
    return LevelGraphicsDisplay(None, 0, 1, 2)


@fixture
def warp_editor(warp_info):
    return LevelGraphicsEditor(None, warp_info)


def test_warp_state_initialization():
    LevelGraphicsState(0, 1, 2)


def test_warp_state_equality():
    assert LevelGraphicsState(0, 1, 2) == LevelGraphicsState(0, 1, 2)


def test_warp_state_inequality():
    assert LevelGraphicsState(0, 1, 2) != LevelGraphicsState(2, 1, 0)


def test_warp_state_inequality_other():
    assert LevelGraphicsState(0, 1, 2) != 1


def test_initialization(qtbot, warp_info):
    LevelGraphicsEditor(None, warp_info)


def test_normal_equality(qtbot, warp_info):
    assert LevelGraphicsEditor(None, warp_info) == LevelGraphicsEditor(None, warp_info)


def test_normal_inequality(qtbot):  # sourcery skip: de-morgan
    assert LevelGraphicsEditor(None, LevelGraphicsState(0, 1, 2)) != LevelGraphicsEditor(
        None, LevelGraphicsState(2, 1, 0)
    )


def test_equality_undo(qtbot, warp_info):
    editor1 = LevelGraphicsEditor(None, warp_info)
    editor2 = LevelGraphicsEditor(None, warp_info)
    editor1.state = LevelGraphicsState(2, 1, 0)
    editor1.undo()
    assert editor1 != editor2

    editor2.state = LevelGraphicsState(2, 1, 0)

    assert editor1 != editor2

    editor2.undo()
    assert editor1 == editor2


def test_equality_redo(qtbot, warp_info):
    editor1 = LevelGraphicsEditor(None, warp_info)
    editor2 = LevelGraphicsEditor(None, warp_info)
    editor1.state = LevelGraphicsState(2, 1, 0)
    editor1.undo()
    editor1.redo()
    assert editor1 != editor2

    editor2.state = LevelGraphicsState(2, 1, 0)

    assert editor1 == editor2

    editor2.undo()
    editor2.redo()
    assert editor1 == editor2


def test_inequality_other(qtbot, warp_editor):
    assert warp_editor != 5


def test_generator_palette_update_generator_palette_changed(qtbot, warp_info):
    editor = LevelGraphicsEditor(None, warp_info)

    with qtbot.waitSignal(editor.generator_palette_changed, timeout=100):
        editor.generator_palette = 7

    assert editor.generator_palette == 7
    assert editor.state.generator_palette == 7


def test_generator_palette_update_state_changed(qtbot, warp_info):
    editor = LevelGraphicsEditor(None, warp_info)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.generator_palette = 7

    assert editor.generator_palette == 7
    assert editor.state.generator_palette == 7


def test_generator_palette_undo_generator_palette_changed(qtbot, warp_info):
    editor = LevelGraphicsEditor(None, warp_info)
    expected = editor.generator_palette
    editor.generator_palette = 3

    with qtbot.waitSignal(editor.generator_palette_changed, timeout=100):
        editor.undo()

    assert editor.generator_palette == expected
    assert editor.state.generator_palette == expected


def test_generator_palette_undo_generator_palette_state_changed(qtbot, warp_info):
    editor = LevelGraphicsEditor(None, warp_info)
    expected = editor.generator_palette
    editor.generator_palette = 7

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.generator_palette == expected
    assert editor.state.generator_palette == expected


def test_generator_palette_redo_generator_palette_changed(qtbot, warp_info):
    editor = LevelGraphicsEditor(None, warp_info)
    editor.generator_palette = 7
    editor.undo()

    with qtbot.waitSignal(editor.generator_palette_changed, timeout=100):
        editor.redo()

    assert editor.generator_palette == 7
    assert editor.state.generator_palette == 7


def test_generator_palette_redo_generator_palette_state_changed(qtbot, warp_info):
    editor = LevelGraphicsEditor(None, warp_info)
    editor.generator_palette = 7
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.generator_palette == 7
    assert editor.state.generator_palette == 7


def test_enemy_palette_update_enemy_palette_changed(qtbot, warp_info):
    editor = LevelGraphicsEditor(None, warp_info)

    with qtbot.waitSignal(editor.enemy_palette_changed, timeout=100):
        editor.enemy_palette = 3

    assert editor.enemy_palette == 3
    assert editor.state.enemy_palette == 3


def test_enemy_palette_update_state_changed(qtbot, warp_info):
    editor = LevelGraphicsEditor(None, warp_info)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.enemy_palette = 3

    assert editor.enemy_palette == 3
    assert editor.state.enemy_palette == 3


def test_enemy_palette_undo_enemy_palette_changed(qtbot, warp_info):
    editor = LevelGraphicsEditor(None, warp_info)
    expected = editor.enemy_palette
    editor.enemy_palette = 3

    with qtbot.waitSignal(editor.enemy_palette_changed, timeout=100):
        editor.undo()

    assert editor.enemy_palette == expected
    assert editor.state.enemy_palette == expected


def test_enemy_palette_undo_state_changed(qtbot, warp_info):
    editor = LevelGraphicsEditor(None, warp_info)
    expected = editor.enemy_palette
    editor.enemy_palette = 3

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.enemy_palette == expected
    assert editor.state.enemy_palette == expected


def test_enemy_palette_redo_enemy_palette_changed(qtbot, warp_info):
    editor = LevelGraphicsEditor(None, warp_info)
    editor.enemy_palette = 3
    editor.undo()

    with qtbot.waitSignal(editor.enemy_palette_changed, timeout=100):
        editor.redo()

    assert editor.enemy_palette == 3
    assert editor.state.enemy_palette == 3


def test_enemy_palette_redo_state_changed(qtbot, warp_info):
    editor = LevelGraphicsEditor(None, warp_info)
    editor.enemy_palette = 3
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.enemy_palette == 3
    assert editor.state.enemy_palette == 3


def test_graphics_set_update_graphics_set_changed(qtbot, warp_info):
    editor = LevelGraphicsEditor(None, warp_info)

    with qtbot.waitSignal(editor.graphics_set_changed, timeout=100):
        editor.graphics_set = 10

    assert editor.graphics_set == 10
    assert editor.state.graphics_set == 10


def test_graphics_set_update_state_changed(qtbot, warp_info):
    editor = LevelGraphicsEditor(None, warp_info)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.graphics_set = 10

    assert editor.graphics_set == 10
    assert editor.state.graphics_set == 10


def test_graphics_set_undo_graphics_set_changed(qtbot, warp_info):
    editor = LevelGraphicsEditor(None, warp_info)
    expected = editor.graphics_set
    editor.graphics_set = 10

    with qtbot.waitSignal(editor.graphics_set_changed, timeout=100):
        editor.undo()

    assert editor.graphics_set == expected
    assert editor.state.graphics_set == expected


def test_graphics_set_undo_state_changed(qtbot, warp_info):
    editor = LevelGraphicsEditor(None, warp_info)
    expected = editor.graphics_set
    editor.graphics_set = 10

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.graphics_set == expected
    assert editor.state.graphics_set == expected


def test_graphics_set_redo_graphics_set_changed(qtbot, warp_info):
    editor = LevelGraphicsEditor(None, warp_info)
    editor.graphics_set = 10
    editor.undo()

    with qtbot.waitSignal(editor.graphics_set_changed, timeout=100):
        editor.redo()

    assert editor.graphics_set == 10
    assert editor.state.graphics_set == 10


def test_graphics_set_redo_state_changed(qtbot, warp_info):
    editor = LevelGraphicsEditor(None, warp_info)
    editor.graphics_set = 10
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.graphics_set == 10
    assert editor.state.graphics_set == 10


def test_display_initialization(qtbot):
    LevelGraphicsDisplay(None, 0, 1, 2)


def test_display_equality(qtbot):
    assert LevelGraphicsDisplay(None, 0, 1, 2) == LevelGraphicsDisplay(None, 0, 1, 2)


def test_display_inequality(qtbot):
    assert LevelGraphicsDisplay(None, 0, 1, 2) != LevelGraphicsDisplay(None, 2, 1, 0)


def test_display_other_inequality(qtbot):
    assert LevelGraphicsDisplay(None, 0, 1, 2) != 5


def test_display_get_generator_palette(qtbot):
    display = LevelGraphicsDisplay(None, 0, 1, 2)
    assert 0 == display.generator_palette


def test_display_set_generator_palette(qtbot, warp_display: LevelGraphicsDisplay):
    warp_display.generator_palette = 5
    assert 5 == warp_display.generator_palette


def test_display_get_enemy_palette(qtbot):
    display = LevelGraphicsDisplay(None, 0, 1, 2)
    assert 1 == display.enemy_palette


def test_display_set_enemy_palette(qtbot, warp_display: LevelGraphicsDisplay):
    warp_display.enemy_palette = 3
    assert 3 == warp_display.enemy_palette


def test_display_get_egraphics_set(qtbot):
    display = LevelGraphicsDisplay(None, 0, 1, 2)
    assert 2 == display.graphics_set


def test_display_set_graphics_set(qtbot, warp_display: LevelGraphicsDisplay):
    warp_display.graphics_set = 5
    assert 5 == warp_display.graphics_set


def test_set_generator_palette(qtbot, warp_editor: LevelGraphicsEditor):
    warp_editor._display.generator_palette = 5
    assert 5 == warp_editor.generator_palette


def test_set_enemy_palette(qtbot, warp_editor: LevelGraphicsEditor):
    warp_editor._display.enemy_palette = 3
    assert 3 == warp_editor.enemy_palette


def test_set_graphics_set(qtbot, warp_editor: LevelGraphicsEditor):
    warp_editor._display.graphics_set = 5
    assert 5 == warp_editor.graphics_set


def test_set_generator_palette_value(qtbot, warp_editor: LevelGraphicsEditor):
    warp_editor._display.generator_palette_editor.setValue(5)
    assert 5 == warp_editor.generator_palette


def test_set_enemy_palette_value(qtbot, warp_editor: LevelGraphicsEditor):
    warp_editor._display.enemy_palette_editor.setValue(3)
    assert 3 == warp_editor.enemy_palette


def test_set_graphics_set_value(qtbot, warp_editor: LevelGraphicsEditor):
    warp_editor._display.graphics_set_editor.setCurrentIndex(5)
    assert 5 == warp_editor.graphics_set
