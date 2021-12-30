from typing import Union

from foundry.game.gfx.objects.EnemyItem import EnemyObject
from foundry.game.gfx.objects.LevelObject import LevelObject


def increment_type(item: Union[LevelObject, EnemyObject]):
    change_type(item, True)


def decrement_type(item: Union[LevelObject, EnemyObject]):
    change_type(item, False)


def change_type(item: Union[LevelObject, EnemyObject], increment: bool):
    if isinstance(item, LevelObject):
        return change_level_object_type(item, increment)
    elif isinstance(item, EnemyObject):
        return change_enemy_object_type(item, increment)


def change_level_object_type(item: LevelObject, increment: bool):
    value = 1 if increment else -1

    new_type = item.obj_index + value

    if new_type < 0 and item.domain > 0:
        new_domain = item.domain - 1
        new_type = 0xF0
    elif new_type > 0xFF and item.domain < 7:
        new_domain = item.domain + 1
        new_type = 0x00
    else:
        new_type = min(0xFF, new_type)
        new_type = max(0, new_type)

        new_domain = item.domain

    item.data[0] &= 0b0001_1111
    item.data[0] |= new_domain << 5
    item.data[2] = new_type

    if item.is_4byte and item.size == 3:
        item.data.append(0)

    item.render()


def change_enemy_object_type(item: EnemyObject, increment: bool):
    item.enemy.type = max(0, min(0xFF, item.obj_index + (1 if increment else -1)))
    item.render()
