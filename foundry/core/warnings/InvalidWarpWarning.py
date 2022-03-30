from foundry.core.warnings.Warning import PydanticWarning, Warning
from foundry.game.gfx.objects.Jump import Jump
from foundry.game.gfx.objects.ObjectLike import ObjectLike


class InvalidWarpWarning(Warning):
    """
    A warning for jumps not having a valid warp.
    """

    def check_object(self, obj: Jump, level=None, *args, **kwargs) -> bool:
        """
        Determines if a jump should emit a warning for not having a place to warp to.

        Parameters
        ----------
        obj : Jump
            The jump to check.
        level : Optional[PydanticLevel]
            The level to check the warps of.

        Returns
        -------
        bool
            If the jump should emit a warning.

        Notes
        -----
        If not level is provided, no warning will be emitted.
        """
        return level is not None and not level.has_next_area

    def get_message(self, obj: ObjectLike) -> str:
        return f"PydanticLevel has {obj}, but no Jump Destination in PydanticLevel Header."


class PydanticInvalidWarpWarning(PydanticWarning):
    """
    A JSON model of a warning that ensures that for a given jump it has a place to warp to.
    """
