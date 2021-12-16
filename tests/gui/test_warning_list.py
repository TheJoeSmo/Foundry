from foundry.game.EnemyDefinitions import get_enemy_metadata


def test_enemy_names(main_window):
    warning_list = main_window.warning_list

    enemy_names = [obj_def.description for obj_def in get_enemy_metadata().__root__]

    for enemy_name in warning_list._enemy_dict.keys():
        assert enemy_name in enemy_names
