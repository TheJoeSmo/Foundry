from enum import Enum
from functools import cache
from json import loads

from pydantic import BaseModel, Field

from foundry import enemy_definitions
from foundry.core.warnings.Warning import Warning
from foundry.game.Definitions import Definition


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


class EnemyDefinition(Definition):
    bmp_width: int = 1
    bmp_height: int = 1
    rect_width: int = 0
    rect_height: int = 0
    rect_x_offset: int = 0
    rect_y_offset: int = 0
    icon_width: int = 0
    icon_height: int = 0
    icon_x_offset: int | None = None
    icon_y_offset: int | None = None
    sprites: list[Sprite] = Field(default_factory=list)
    blocks: list[int] = Field(default_factory=list)
    pages: list[int] = Field(default_factory=list)
    orientation: GeneratorType = GeneratorType.SINGLE_BLOCK_OBJECT
    check_level_bounds: bool = True
    check_compatibility: bool = True

    @property
    def suggested_icon_width(self) -> int:
        """
        Provides the suggested icon width, as the icon width my not be set.

        Returns
        -------
        int
            The suggested icon width.
        """
        width = self.icon_width
        if not width:
            width = self.rect_width
            if not width:
                width = self.bmp_width
                if GeneratorType.SINGLE_SPRITE_OBJECT == self.orientation:
                    width //= 2
        return width

    @property
    def suggested_icon_height(self) -> int:
        """
        Provides the suggested icon height, as the icon height my not be set.

        Returns
        -------
        int
            The suggested icon height.
        """
        height = self.icon_height
        if not height:
            height = self.rect_height
            if not height:
                height = self.bmp_height
        return height

    @property
    def suggested_icon_x_offset(self) -> int:
        """
        Provides the suggested icon x offset, as the icon x offset may be None.

        Returns
        -------
        int
            The suggested icon x offset.
        """
        offset = self.icon_x_offset
        if offset is None:
            offset = self.rect_x_offset * 16
        return offset

    @property
    def suggested_icon_y_offset(self) -> int:
        """
        Provides the suggested icon y offset, as the icon y offset may be None.

        Returns
        -------
        int
            The suggested icon y offset.
        """
        offset = self.icon_y_offset
        if offset is None:
            offset = self.rect_y_offset * 16
        return offset

    def get_warnings(self) -> list[Warning]:
        warnings: list[Warning] = [warning.to_warning() for warning in self.warnings.copy()]  # type: ignore
        if self.check_compatibility:
            from foundry.core.warnings.EnemyCompatibilityWarning import (
                EnemyCompatibilityWarning,
            )

            warnings.append(EnemyCompatibilityWarning())
        if self.check_level_bounds:
            from foundry.core.warnings.OutsideLevelBoundsWarning import (
                OutsideLevelBoundsWarning,
            )

            warnings.append(OutsideLevelBoundsWarning())
        return warnings


class EnemyDefinitions(BaseModel):
    __root__: list[EnemyDefinition]


@cache
def get_enemy_metadata() -> EnemyDefinitions:
    with open(enemy_definitions) as f:
        return EnemyDefinitions(__root__=loads(f.read()))
