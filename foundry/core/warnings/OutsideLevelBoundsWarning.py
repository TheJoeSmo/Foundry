from foundry.core.warnings.Warning import PydanticWarning, Warning
from foundry.game.gfx.objects.ObjectLike import ObjectLike


class OutsideLevelBoundsWarning(Warning):
    """
    A warning for objects going outside the level bounds.
    """

    def check_object(self, obj: ObjectLike, level=None, *args, **kwargs) -> bool:
        """
        Determines if an object should emit a warning for being outside the level bounds.

        Parameters
        ----------
        obj : ObjectLike
            The object to check.
        level : Optional[PydanticLevel]
            The level to check the bounds of.

        Returns
        -------
        bool
            If the object should emit a warning.

        Notes
        -----
        If not level is provided, no warning will be emitted.
        """
        if level is None:
            return False
        return not level.get_rect().contains(obj.get_rect())

    def get_message(self, obj: ObjectLike) -> str:
        return f"{obj} is outside of level bounds."


class PydanticOutsideLevelBoundsWarning(PydanticWarning):
    """
    A JSON model of a warning that ensures that an object is inside the bounds of the level.
    """
