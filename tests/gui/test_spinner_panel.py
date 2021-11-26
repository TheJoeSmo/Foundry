from foundry.game.gfx.objects.LevelObject import LevelObject


def test_object_selected(main_window):
    # GIVEN the main window containing the spinner panel
    level_ref = main_window.manager.controller.level_ref

    # WHEN a level object or enemy is selected and the spinner is updated
    level_obj = level_ref.level.objects[0]
    enemy = level_ref.level.enemies[0]

    for obj in [level_obj, enemy]:
        obj.selected = True

        assert level_ref.selected_objects == [obj]

        main_window.spinner_panel.update()

        # THEN the spinners are set accordingly
        type_spinner = main_window.spinner_panel.spin_type
        domain_spinner = main_window.spinner_panel.spin_domain
        length_spinner = main_window.spinner_panel.spin_length

        assert type_spinner.isEnabled() and type_spinner.value() == obj.obj_index
        assert domain_spinner.isEnabled() == isinstance(obj, LevelObject) and domain_spinner.value() == obj.domain
        assert length_spinner.isEnabled() == obj.is_4byte and length_spinner.value() == 0

        obj.selected = False
