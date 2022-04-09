from pytest import fixture

from foundry.game.level.util import DisplayInformation, Level
from foundry.gui.LevelInformationEditor import (
    LevelInformationEditor,
    LevelInformationEditorDisplay,
)


@fixture
def level_info_empty():
    return Level(DisplayInformation(None, None, []), 0, 1, 2, 3, 4)


@fixture
def level_info():
    return Level(DisplayInformation("name", "description", []), 0, 1, 2, 3, 4)


@fixture
def level_display():
    return LevelInformationEditorDisplay(None, "name", "description", 3, 4)


@fixture
def level_editor(level_info):
    return LevelInformationEditor(None, level_info)


def test_empty_initialization(qtbot, level_info_empty):
    LevelInformationEditor(None, level_info_empty)


def test_initialization(qtbot, level_info):
    LevelInformationEditor(None, level_info)


def test_empty_equality(qtbot):
    assert LevelInformationEditor(
        None, Level(DisplayInformation(None, None, []), 0, 1, 2, 3, 4)
    ) == LevelInformationEditor(None, Level(DisplayInformation(None, None, []), 0, 1, 2, 3, 4))


def test_normal_equality(qtbot):
    assert LevelInformationEditor(
        None, Level(DisplayInformation("name", "description", []), 0, 1, 2, 3, 4)
    ) == LevelInformationEditor(None, Level(DisplayInformation("name", "description", []), 0, 1, 2, 3, 4))


def test_normal_empty_inequality(qtbot):  # sourcery skip: de-morgan
    assert LevelInformationEditor(
        None, Level(DisplayInformation("name", "description", []), 0, 1, 2, 3, 4)
    ) != LevelInformationEditor(None, Level(DisplayInformation(None, None, []), 0, 1, 2, 3, 4))


def test_empty_normal_inequality(qtbot):  # sourcery skip: de-morgan
    assert LevelInformationEditor(
        None, Level(DisplayInformation(None, None, []), 0, 1, 2, 3, 4)
    ) != LevelInformationEditor(None, Level(DisplayInformation("name", "description", []), 0, 1, 2, 3, 4))


def test_equality_undo(qtbot):
    editor1 = LevelInformationEditor(None, Level(DisplayInformation("name", "description", []), 0, 1, 2, 3, 4))
    editor2 = LevelInformationEditor(None, Level(DisplayInformation("name", "description", []), 0, 1, 2, 3, 4))
    editor1.state = ("new name", "new description", 1, 2)
    editor1.undo()
    assert editor1 != editor2

    editor2.state = ("new name", "new description", 1, 2)

    assert editor1 != editor2

    editor2.undo()
    assert editor1 == editor2


def test_equality_redo(qtbot):
    editor1 = LevelInformationEditor(None, Level(DisplayInformation("name", "description", []), 0, 1, 2, 3, 4))
    editor2 = LevelInformationEditor(None, Level(DisplayInformation("name", "description", []), 0, 1, 2, 3, 4))
    editor1.state = ("new name", "new description", 1, 2)
    editor1.undo()
    editor1.redo()
    assert editor1 != editor2

    editor2.state = ("new name", "new description", 1, 2)

    assert editor1 == editor2

    editor2.undo()
    editor2.redo()
    assert editor1 == editor2


def test_inequality_other(qtbot):
    assert LevelInformationEditor(None, Level(DisplayInformation("name", "description", []), 0, 1, 2, 3, 4)) != 5


def test_name_updates_name(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)
    editor.name = "new name"
    assert editor.name == "new name"
    assert editor.level.display_information.name == "new name"


def test_name_update_name_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)

    with qtbot.waitSignal(editor.name_changed, timeout=100):
        editor.name = "new name"

    assert editor.name == "new name"
    assert editor.level.display_information.name == "new name"


def test_name_update_state_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.name = "new name"

    assert editor.name == "new name"
    assert editor.level.display_information.name == "new name"


def test_name_undo_name_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)
    editor.name = "new name"

    with qtbot.waitSignal(editor.name_changed, timeout=100):
        editor.undo()

    assert editor.name == "name"
    assert editor.level.display_information.name == "name"


def test_name_undo_state_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)
    editor.name = "new name"

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.name == "name"
    assert editor.level.display_information.name == "name"


def test_name_redo_name_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)
    editor.name = "new name"
    editor.undo()

    with qtbot.waitSignal(editor.name_changed, timeout=100):
        editor.redo()

    assert editor.name == "new name"
    assert editor.level.display_information.name == "new name"


def test_name_redo_state_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)
    editor.name = "new name"
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.name == "new name"
    assert editor.level.display_information.name == "new name"


def test_description_update_description_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)

    with qtbot.waitSignal(editor.description_changed, timeout=100):
        editor.description = "new description"

    assert editor.description == "new description"
    assert editor.level.display_information.description == "new description"


def test_description_update_state_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.description = "new description"

    assert editor.description == "new description"
    assert editor.level.display_information.description == "new description"


def test_description_undo_description_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)
    editor.description = "new description"

    with qtbot.waitSignal(editor.description_changed, timeout=100):
        editor.undo()

    assert editor.description == "description"
    assert editor.level.display_information.description == "description"


def test_description_undo_state_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)
    editor.description = "new description"

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.description == "description"
    assert editor.level.display_information.description == "description"


def test_description_redo_description_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)
    editor.description = "new description"
    editor.undo()

    with qtbot.waitSignal(editor.description_changed, timeout=100):
        editor.redo()

    assert editor.description == "new description"
    assert editor.level.display_information.description == "new description"


def test_description_redo_state_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)
    editor.description = "new description"
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.description == "new description"
    assert editor.level.display_information.description == "new description"


def test_generator_space_update_generator_space_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)

    with qtbot.waitSignal(editor.generator_space_changed, timeout=100):
        editor.generator_space = 10

    assert editor.generator_space == 10
    assert editor.level.generator_size == 10


def test_generator_space_update_state_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.generator_space = 10

    assert editor.generator_space == 10
    assert editor.level.generator_size == 10


def test_generator_space_undo_generator_space_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)
    expected = editor.generator_space
    editor.generator_space = 10

    with qtbot.waitSignal(editor.generator_space_changed, timeout=100):
        editor.undo()

    assert editor.generator_space == expected
    assert editor.level.generator_size == expected


def test_generator_space_undo_generator_space_state_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)
    expected = editor.generator_space
    editor.generator_space = 10

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.generator_space == expected
    assert editor.level.generator_size == expected


def test_generator_space_redo_generator_space_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)
    editor.generator_space = 10
    editor.undo()

    with qtbot.waitSignal(editor.generator_space_changed, timeout=100):
        editor.redo()

    assert editor.generator_space == 10
    assert editor.level.generator_size == 10


def test_generator_space_redo_generator_space_state_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)
    editor.generator_space = 10
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.generator_space == 10
    assert editor.level.generator_size == 10


def test_enemy_space_update_enemy_space_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)

    with qtbot.waitSignal(editor.enemy_space_changed, timeout=100):
        editor.enemy_space = 10

    assert editor.enemy_space == 10
    assert editor.level.enemy_size == 10


def test_enemy_space_update_state_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.enemy_space = 10

    assert editor.enemy_space == 10
    assert editor.level.enemy_size == 10


def test_enemy_space_undo_enemy_space_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)
    expected = editor.enemy_space
    editor.enemy_space = 10

    with qtbot.waitSignal(editor.enemy_space_changed, timeout=100):
        editor.undo()

    assert editor.enemy_space == expected
    assert editor.level.enemy_size == expected


def test_enemy_space_undo_state_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)
    expected = editor.enemy_space
    editor.enemy_space = 10

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.undo()

    assert editor.enemy_space == expected
    assert editor.level.enemy_size == expected


def test_enemy_space_redo_enemy_space_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)
    editor.enemy_space = 10
    editor.undo()

    with qtbot.waitSignal(editor.enemy_space_changed, timeout=100):
        editor.redo()

    assert editor.enemy_space == 10
    assert editor.level.enemy_size == 10


def test_enemy_space_redo_state_changed(qtbot, level_info):
    editor = LevelInformationEditor(None, level_info)
    editor.enemy_space = 10
    editor.undo()

    with qtbot.waitSignal(editor.state_changed, timeout=100):
        editor.redo()

    assert editor.enemy_space == 10
    assert editor.level.enemy_size == 10


def test_display_initialization(qtbot):
    LevelInformationEditorDisplay(None, "name", "description", 3, 4)


def test_display_equality(qtbot):
    assert LevelInformationEditorDisplay(None, "name", "description", 3, 4) == LevelInformationEditorDisplay(
        None, "name", "description", 3, 4
    )


def test_display_inequality(qtbot):
    assert LevelInformationEditorDisplay(None, "name", "description", 3, 4) != LevelInformationEditorDisplay(
        None, "name", "description", 3, 5
    )


def test_display_other_inequality(qtbot):
    assert LevelInformationEditorDisplay(None, "name", "description", 3, 4) != 5


def test_display_get_name(qtbot):
    display = LevelInformationEditorDisplay(None, "name", "description", 3, 4)
    assert "name" == display.name


def test_display_set_name(qtbot, level_display: LevelInformationEditorDisplay):
    level_display.name = "new name"
    assert "new name" == level_display.name


def test_display_get_description(qtbot):
    display = LevelInformationEditorDisplay(None, "name", "description", 3, 4)
    assert "description" == display.description


def test_display_set_description(qtbot, level_display: LevelInformationEditorDisplay):
    level_display.description = "new description"
    assert "new description" == level_display.description


def test_display_get_generator_space(qtbot):
    display = LevelInformationEditorDisplay(None, "name", "description", 3, 4)
    assert 3 == display.generator_space


def test_display_set_generator_space(qtbot, level_display: LevelInformationEditorDisplay):
    level_display.generator_space = 5
    assert 5 == level_display.generator_space


def test_display_get_enemy_space(qtbot):
    display = LevelInformationEditorDisplay(None, "name", "description", 3, 4)
    assert 4 == display.enemy_space


def test_display_set_enemy_space(qtbot, level_display: LevelInformationEditorDisplay):
    level_display.enemy_space = 5
    assert 5 == level_display.enemy_space


def test_set_name(qtbot, level_editor: LevelInformationEditor):
    level_editor._display.name = "new name"
    assert "new name" == level_editor.name


def test_set_description(qtbot, level_editor: LevelInformationEditor):
    level_editor._display.description = "new description"
    assert "new description" == level_editor.description


def test_set_generator_space(qtbot, level_editor: LevelInformationEditor):
    level_editor._display.generator_space = 5
    assert 5 == level_editor.generator_space


def test_set_enemy_space(qtbot, level_editor: LevelInformationEditor):
    level_editor._display.enemy_space = 5
    assert 5 == level_editor.enemy_space


def test_set_name_test(qtbot, level_editor: LevelInformationEditor):
    level_editor._display.name_editor.setText("new name")
    assert "new name" == level_editor.name


def test_set_description_text(qtbot, level_editor: LevelInformationEditor):
    level_editor._display.description_editor.setText("new description")
    assert "new description" == level_editor.description


def test_set_generator_space_value(qtbot, level_editor: LevelInformationEditor):
    level_editor._display.generator_space_editor.setValue(5)
    assert 5 == level_editor.generator_space


def test_set_enemy_space_value(qtbot, level_editor: LevelInformationEditor):
    level_editor._display.enemy_space_editor.setValue(5)
    assert 5 == level_editor.enemy_space
