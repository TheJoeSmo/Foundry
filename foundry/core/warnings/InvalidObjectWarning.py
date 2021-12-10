from foundry.core.warnings.Warning import PydanticWarning, Warning
from foundry.game.gfx.objects.ObjectLike import ObjectLike


class InvalidObjectWarning(Warning):
    """
    A warning for an object that is invalid.
    """

    def get_message(self, obj: ObjectLike, *args, **kwargs) -> str:
        return f"Object at {obj.position.x}, {obj.position.y} will likely cause the game to crash"


class PydanticInvalidObjectWarning(PydanticWarning):
    """
    A JSON model of a warning that notifies the user of an invalid object.
    """
