from foundry.core.warnings.Warning import PydanticWarning, Warning
from foundry.game.gfx.objects.LevelObject import LevelObject
from foundry.game.gfx.objects.ObjectLike import ObjectLike


class ExtendToGroundWarning(Warning):
    """
    A warning to ensure that an object does not extend to the ground.
    """

    def check_object(self, obj: LevelObject, *args, **kwargs) -> bool:
        """
        Determines if the object should emit a warning for extending to the ground.

        Parameters
        ----------
        obj : LevelObject
            The object to check.

        Returns
        -------
        bool
            If the object should emit a warning.
        """
        return obj.position.y + obj.rendered_size.height == 27

    def get_message(self, obj: ObjectLike) -> str:
        return f"{obj} extends until the level bottom. This can crash the game."


class PydanticExtendToGroundWarning(PydanticWarning):
    """
    A JSON model of a warning that checks that an object does not extend to the ground.
    """
