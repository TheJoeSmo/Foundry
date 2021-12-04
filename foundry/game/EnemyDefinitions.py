from enum import Enum
from json import loads

from pydantic import BaseModel, Field

from foundry import enemy_definitions


class GeneratorType(int, Enum):
    """
    The various different ways enemies can be represented inside the game.
    """

    SINGLE_SPRITE_OBJECT = 0
    SINGLE_BLOCK_OBJECT = 9
    CENTERED = 10


class Sprite(BaseModel):
    """
    Defines a given sprite and its properties
    """

    index: int
    palette_index: int = 1
    x_offset: int = 0
    y_offset: int = 0
    horizontal_mirror: bool = False
    vertical_mirror: bool = False


class EnemyDefinition(BaseModel):
    bmp_width: int = 1
    bmp_height: int = 1
    rect_width: int = 0
    rect_height: int = 0
    rect_x_offset: int = 0
    rect_y_offset: int = 0
    sprites: list[Sprite] = Field(default_factory=list)
    blocks: list[int] = Field(default_factory=list)
    pages: list[int] = Field(default_factory=list)
    orientation: GeneratorType = GeneratorType.SINGLE_BLOCK_OBJECT
    description: str

    class Config:
        use_enum_values = True


class EnemyDefinitions(BaseModel):
    __root__: list[EnemyDefinition]


with open(enemy_definitions, "r") as f:
    enemy_definitions = EnemyDefinitions(__root__=loads(f.read()))
