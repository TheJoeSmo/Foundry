from foundry.core.warnings.Warning import PydanticWarning, Warning
from foundry.game.gfx.objects.EnemyItem import EnemyObject
from foundry.game.gfx.objects.ObjectLike import ObjectLike


def find_incompatibilities(enemies: list[EnemyObject]) -> tuple[bool, bool]:
    """
    Determines if there are any incompatibilities with enemy graphics.

    Parameters
    ----------
    enemies : list[EnemyObject]
        The enemies to check compatibility of.

    Returns
    -------
    tuple[bool, bool]
        If there are any incompatibilities between the 5th and 6th page, respectively.
    """
    primary_incompatibilities = set()
    secondary_incompatibilities = set()
    if not enemies:
        return False, False
    for enemy in enemies[:-1]:
        pages = enemy.definition.pages
        if len(pages) >= 3 and pages[2] != 0:
            primary_incompatibilities.add(pages[2])
        if len(pages) >= 4 and pages[3] != 0:
            secondary_incompatibilities.add(pages[3])
    last_def = enemies[-1].definition
    has_primary_incompatibilities = (
        bool(primary_incompatibilities)
        and len(last_def.pages) >= 3
        and last_def.pages[2] not in primary_incompatibilities
        and last_def.pages[2] != 0
    )
    has_secondary_incompatibilities = (
        bool(secondary_incompatibilities)
        and len(last_def.pages) >= 4
        and last_def.pages[3] not in secondary_incompatibilities
        and last_def.pages[3] != 0
    )
    return has_primary_incompatibilities, has_secondary_incompatibilities


class EnemyCompatibilityWarning(Warning):
    """
    A warning to ensure that an that checks that the graphics of enemies do not conflict.
    """

    def check_object(self, obj: EnemyObject, level=None, index=0, *args, **kwargs) -> bool:
        """
        Determines if the object should emit a warning for having graphical conflicts.

        Parameters
        ----------
        obj : EnemyObject
            The object to check.
        level : PydanticLevel
            The level the object is housed inside.
        index : int
            The index into the level enemies obj is housed.

        Returns
        -------
        bool
            If the object should emit a warning.
        """
        if level is None:
            return False
        return any(find_incompatibilities(level.enemies[:index]))

    def get_message(self, obj: ObjectLike) -> str:
        return f"{obj} may have graphical conflicts with other enemies inside the level."


class PydanticEnemyCompatibilityWarning(PydanticWarning):
    """
    A JSON model of a warning that checks that the graphics of enemies do not conflict.
    """
