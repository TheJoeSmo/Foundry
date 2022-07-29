from json import loads

from attr import attrs
from pydantic import BaseModel

from foundry import data_dir, default_levels_path


@attrs(auto_attribs=True, slots=True, frozen=True)
class Location:
    """
    A representation of a location of a level.

    world: int
        The world the level is located inside.
    index: int
        The index the level is inside the world.
    """

    world: int
    index: int


@attrs(auto_attribs=True, slots=True, frozen=True)
class DisplayInformation:
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

    name: str | None
    description: str | None
    locations: list[Location]


@attrs(auto_attribs=True, slots=True, frozen=True, repr=False)
class Level:
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

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}({self.display_information}, {hex(self.generator_pointer)}, "
            + f"{hex(self.enemy_pointer)}, {self.tileset}, {self.generator_size}, {self.enemy_size})"
        )


class PydanticLocation(BaseModel):
    """
    A representation of a location of a level.

    world: int
        The world the level is located inside.
    index: int
        The index the level is inside the world.
    """

    world: int
    index: int

    def to_location(self) -> Location:
        """
        Converts the instance to a dataclass to be more easily modified.

        Returns
        -------
        Location
            The location representation of this instance.
        """
        return Location(self.world, self.index)


class PydanticDisplayInformation(BaseModel):
    """
    The display information to nicely sort levels.

    Attributes
    ----------
    name: Optional[str]
        The name of the level.
    description: Optional[str]
        The description of the level.
    locations: list[PydanticLocation]
        The locations that the level is inside.
    """

    name: str | None
    description: str | None
    locations: list[PydanticLocation]

    def to_display_information(self) -> DisplayInformation:
        """
        Converts the instance to a dataclass to be more easily modified.

        Returns
        -------
        DisplayInformation
            The display information representation of this instance.
        """
        return DisplayInformation(self.name, self.description, [loc.to_location() for loc in self.locations])


class PydanticLevel(BaseModel):
    """
    The representation of a level inside the game.

    Attributes
    ----------
    display_information: PydanticDisplayInformation
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

    display_information: PydanticDisplayInformation
    generator_pointer: int
    enemy_pointer: int
    tileset: int
    generator_size: int
    enemy_size: int

    def to_level(self) -> Level:
        """
        Converts the instance to a dataclass to be more easily modified.

        Returns
        -------
        Level
            The level representation of this instance.
        """
        return Level(
            self.display_information.to_display_information(),
            self.generator_pointer,
            self.enemy_pointer,
            self.tileset,
            self.generator_size,
            self.enemy_size,
        )


def to_pydantic_location(location: Location) -> PydanticLocation:
    """
    Converts a location to a pydantic location.

    Parameters
    ----------
    location : Location
        The location to convert.

    Returns
    -------
    PydanticLocation
        The pydantic equivelant of the location.
    """
    return PydanticLocation(world=location.world, index=location.index)


def to_pydantic_display_information(display_information: DisplayInformation) -> PydanticDisplayInformation:
    """
    Converts a display information to a pydantic displayer information.

    Parameters
    ----------
    display_information : DisplayInformation
        The display information to convert.

    Returns
    -------
    PydanticDisplayInformation
        The pydantic equivelant of the display information.
    """
    return PydanticDisplayInformation(
        name=display_information.name,
        description=display_information.description,
        locations=[to_pydantic_location(loc) for loc in display_information.locations],
    )


def to_pydantic_level(level: Level) -> PydanticLevel:
    """
    Converts a level to a pydantic level.

    Parameters
    ----------
    level : Level
        The level to convert.

    Returns
    -------
    PydanticLevel
        The pydantic equivelant of the level.
    """
    return PydanticLevel(
        display_information=to_pydantic_display_information(level.display_information),
        generator_pointer=level.generator_pointer,
        enemy_pointer=level.enemy_pointer,
        tileset=level.tileset,
        generator_size=level.generator_size,
        enemy_size=level.enemy_size,
    )


def generate_default_level_information() -> list[Level]:
    """
    Generates a default assortment of levels to be applied to a new file.

    Returns
    -------
    list[Level]
        A list of levels that the base game contains.
    """
    with open(default_levels_path) as f:
        return [PydanticLevel(**level).to_level() for level in loads(f.read())]


def get_world_levels(world: int, levels: list[Level]) -> list[Level]:
    """
    Provides every level that is inside a given world.

    Parameters
    ----------
    world : int
        The world to select levels from.
    levels : list[PydanticLevel]
        The index of levels to find levels from.

    Returns
    -------
    list[PydanticLevel]
        A sub-list of levels which contains only the levels that were inside the given world.

    Notes
    -----
    For each level.display_information.index, there will only be a single level inside the return.
    """
    world_levels = {}
    for level in levels:
        for location in level.display_information.locations:
            if location.world == world:
                world_levels[location.index] = level
    return [element[1] for element in sorted(world_levels.items(), key=lambda item: item[0])]


def find_level_by_pointers(levels: list[Level], generator_pointer: int, enemy_pointer: int) -> Level | None:
    """
    Finds a level by its pointers.

    Parameters
    ----------
    levels : list[Level]
        The levels to search through.
    generator_pointer : int
        The generator pointer of the level to find.
    enemy_pointer : int
        The enemy pointer of the level to find.

    Returns
    -------
    Optional[Level]
        The level, if one is found.
    """
    for level in levels:
        if level.generator_pointer == generator_pointer and level.enemy_pointer == enemy_pointer:
            return level


def get_level_index(levels: list[Level], generator_pointer: int, enemy_pointer: int) -> int:
    """
    Finds a level by its pointers and sets it to the incoming value.

    Parameters
    ----------
    levels : list[Level]
        The levels to search through.
    generator_pointer : int
        The generator pointer of the level to find.
    enemy_pointer : int
        The enemy pointer of the level to find.

    Returns
    -------
    int
        The index of the level
    """
    for index, level in enumerate(levels):
        if level.generator_pointer == generator_pointer and level.enemy_pointer == enemy_pointer:
            return index


def get_worlds(levels: list[PydanticLevel]) -> int:
    """
    Determines the amount of worlds there are inside the game.

    Parameters
    ----------
    levels : list[PydanticLevel]
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


def load_level_offsets() -> list[PydanticLevel]:
    with open(data_dir.joinpath("levels.json")) as f:
        return [PydanticLevel(**level) for level in loads(f.read())]
