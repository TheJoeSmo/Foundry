from functools import cache

from foundry.core.warnings.Warning import PydanticWarning, Warning
from foundry.core.warnings.WarningType import WarningType


@cache
def type_to_pydantic_warning() -> dict[WarningType, type[PydanticWarning]]:
    """
    Provide a dictionary to easily convert between a given warning type and pydantic warning

    Returns
    -------
    dict[WarningType, Type[PydanticWarning]]
        A dict containing a warning type and its corresponding pydantic warning.
    """
    from foundry.core.warnings.EnemyCompatibilityWarning import (
        PydanticEnemyCompatibilityWarning,
    )
    from foundry.core.warnings.ExtendToGroundWarning import (
        PydanticExtendToGroundWarning,
    )
    from foundry.core.warnings.InvalidObjectWarning import PydanticInvalidObjectWarning
    from foundry.core.warnings.InvalidPositionWarning import (
        PydanticInvalidPositionWarning,
    )
    from foundry.core.warnings.InvalidSizeWarning import PydanticInvalidSizeWarning
    from foundry.core.warnings.InvalidWarpWarning import PydanticInvalidWarpWarning
    from foundry.core.warnings.OutsideLevelBoundsWarning import (
        PydanticOutsideLevelBoundsWarning,
    )

    return {
        WarningType.enemy_compatibility: PydanticEnemyCompatibilityWarning,
        WarningType.invalid_extension_to_ground: PydanticExtendToGroundWarning,
        WarningType.invalid_type: PydanticInvalidObjectWarning,
        WarningType.invalid_position: PydanticInvalidPositionWarning,
        WarningType.invalid_size: PydanticInvalidSizeWarning,
        WarningType.invalid_warp: PydanticInvalidWarpWarning,
        WarningType.outside_level_bounds: PydanticOutsideLevelBoundsWarning,
    }


@cache
def type_to_warning() -> dict[WarningType, type[Warning]]:
    """
    Provide a dictionary to easily convert between a given warning type and warning

    Returns
    -------
    dict[WarningType, Type[Warning]]
        A dict containing a warning type and its corresponding warning.
    """
    from foundry.core.warnings.EnemyCompatibilityWarning import (
        EnemyCompatibilityWarning,
    )
    from foundry.core.warnings.ExtendToGroundWarning import ExtendToGroundWarning
    from foundry.core.warnings.InvalidObjectWarning import InvalidObjectWarning
    from foundry.core.warnings.InvalidPositionWarning import InvalidPositionWarning
    from foundry.core.warnings.InvalidSizeWarning import InvalidSizeWarning
    from foundry.core.warnings.InvalidWarpWarning import InvalidWarpWarning
    from foundry.core.warnings.OutsideLevelBoundsWarning import (
        OutsideLevelBoundsWarning,
    )

    return {
        WarningType.enemy_compatibility: EnemyCompatibilityWarning,
        WarningType.invalid_extension_to_ground: ExtendToGroundWarning,
        WarningType.invalid_type: InvalidObjectWarning,
        WarningType.invalid_position: InvalidPositionWarning,
        WarningType.invalid_size: InvalidSizeWarning,
        WarningType.invalid_warp: InvalidWarpWarning,
        WarningType.outside_level_bounds: OutsideLevelBoundsWarning,
    }


def convert_pydantic_to_warning(warning: PydanticWarning) -> type[Warning]:
    """
    Provides the class alternative for a given pydantic warning.

    Parameters
    ----------
    warning : PydanticWarning
        The pydantic warning to find the warning alternative of.

    Returns
    -------
    Type[Warning]
        The class that represents the pydantic warning.
    """
    return type_to_warning()[warning.type]
