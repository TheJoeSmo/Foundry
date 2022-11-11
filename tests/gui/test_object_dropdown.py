from foundry.smb3parse.objects.tileset import HILLY_OBJECT_SET
from tests.conftest import level_1_2_enemy_address, level_1_2_object_address


def test_object_update_on_level_change(main_window):
    # GIVEN the main window and the object dropdown
    object_dropdown = main_window.object_dropdown

    original_tileset = main_window.manager.controller.level_ref.level.tileset_number
    original_first_object = object_dropdown.itemText(0)

    # WHEN the level is changed
    main_window.manager.controller.update_level(
        "Level 1-2", level_1_2_object_address, level_1_2_enemy_address, HILLY_OBJECT_SET
    )

    assert original_tileset != main_window.manager.controller.level_ref.level.tileset_number

    # THEN the objects in the dropdown should be changed
    new_first_object = object_dropdown.itemText(0)

    assert original_first_object != new_first_object, "Objects didn't change."
