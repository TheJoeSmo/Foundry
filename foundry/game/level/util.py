from typing import Optional

from pydantic import BaseModel

from foundry import data_dir


class Location(BaseModel):
    """
    A representation of a location of a level.

    world: int
        The world the level is located inside.
    index: int
        The index the level is inside the world.
    """

    world: int
    index: int


class DisplayInformation(BaseModel):
    """
    The display information to nicely sort levels.

    Attributes
    ----------
    name: Optional[str]
        The name of the level.
    description: Optional[str]
        The description of the level.
    locations: list[Location]
        The locations that the level is inside.
    """

    name: Optional[str]
    description: Optional[str]
    locations: list[Location]


class Level(BaseModel):
    """
    The representation of a level inside the game.

    Attributes
    ----------
    display_information: DisplayInformation
        Useful information regarding the level to make it human usable.
    generator_pointer: int
        The location this level's generators are located at.
    enemy_pointer: int
        The location this level's enemies are located at.
    tileset: int
        The tileset of the this level.
    """

    display_information: DisplayInformation
    generator_pointer: int
    enemy_pointer: int
    tileset: int


def load_level_offsets() -> tuple[list[Level], list[int]]:
    offsets = []
    world_indexes = []

    with open(data_dir.joinpath("levels.dat"), "r") as level_data:
        for line_no, line in enumerate(level_data.readlines()):
            data = line.rstrip("\n").split(",")

            numbers = [int(_hex, 16) for _hex in data[0:5]]
            level_name = data[5]

            game_world, level_in_world, rom_level_offset, enemy_offset, real_obj_set = numbers

            level = Level(
                display_information=DisplayInformation(
                    name=level_name, locations=[Location(world=game_world, index=level_in_world)]
                ),
                generator_pointer=rom_level_offset,
                enemy_pointer=enemy_offset,
                tileset=real_obj_set,
            )

            offsets.append(level)

            for location in level.display_information.locations:
                if location.world > 0 and location.index == 1:
                    world_indexes.append(line_no)

    return offsets, world_indexes
