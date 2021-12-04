from enum import Enum
from json import loads

from pydantic import BaseModel

from foundry import enemy_definitions


class GeneratorType(int, Enum):
    """
    The various different ways enemies can be represented inside the game.
    """

    SINGLE_BLOCK_OBJECT = 9
    CENTERED = 10


class EnemyDefinition(BaseModel):
    bmp_width: int
    bmp_height: int
    blocks: list[int]
    orientation: GeneratorType
    description: str

    class Config:
        use_enum_values = True


class EnemyDefinitions(BaseModel):
    __root__: list[EnemyDefinition]


with open(enemy_definitions, "r") as f:
    enemy_definitions = EnemyDefinitions(__root__=loads(f.read()))
