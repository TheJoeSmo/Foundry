import pytest

from foundry.smb3parse.objects.object_set import ENEMY_ITEM_OBJECT_SET, ObjectSet


def test_enemy_item_set_value_error():
    enemy_item_set = ObjectSet(ENEMY_ITEM_OBJECT_SET)

    with pytest.raises(ValueError):
        assert enemy_item_set.ending_graphic_offset

    with pytest.raises(ValueError):
        enemy_item_set.is_in_level_range(0)
