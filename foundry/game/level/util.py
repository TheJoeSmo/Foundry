from json import loads
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
    generator_size: int
        The amount of space the generator data takes inside the game.
    enemy_size: int
        The amount of space the enemy data takes inside the game.
    """

    display_information: DisplayInformation
    generator_pointer: int
    enemy_pointer: int
    tileset: int
    generator_size: int
    enemy_size: int


def get_world_levels(world: int, levels: list[Level]) -> list[Level]:
    """
    Provides every level that is inside a given world.

    Parameters
    ----------
    world : int
        The world to select levels from.
    levels : list[Level]
        The index of levels to find levels from.

    Returns
    -------
    list[Level]
        A sub-list of levels which contains only the levels that were inside the given world.

    Notes
    -----
    For each level.display_information.index, there will only be a single level inside the return.
    """
    world_levels = {}
    for level in levels:
        for location in level.display_information.locations:
            if location.world == world:
                world_levels.update({location.index: level})
    return [element[1] for element in sorted(world_levels.items(), key=lambda item: item[0])]


def get_worlds(levels: list[Level]) -> int:
    """
    Determines the amount of worlds there are inside the game.

    Parameters
    ----------
    levels : list[Level]
        The levels to find worlds from.

    Returns
    -------
    int
        The amount of worlds there are.
    """
    worlds = 0
    for level in levels:
        if level.tileset == 0:
            worlds += 1
    return worlds


def load_level_offsets() -> list[Level]:
    with open(data_dir.joinpath("levels.json"), "r") as f:
        return [Level(**level) for level in loads(f.read())]
