from attr import attrs

from foundry.core.warnings.Warning import PydanticWarning, Warning
from foundry.game.gfx.objects.ObjectLike import ObjectLike


@attrs(slots=True, frozen=True, auto_attribs=True)
class InvalidPositionWarning(Warning):
    """
    A warning for an object exceeding its valid positional range.
    """

    max_x: int | None = None
    min_x: int | None = None
    max_y: int | None = None
    min_y: int | None = None

    def check_object(self, obj: ObjectLike, *args, **kwargs) -> bool:
        """
        Determines if the object should emit a warning for having an invalid point.

        Parameters
        ----------
        obj : ObjectLike
            The object to check.

        Returns
        -------
        bool
            If the object should emit a warning.
        """
        return (
            self.max_x is not None
            and obj.position.x > self.max_x
            or self.min_x is not None
            and obj.position.x < self.min_x
            or self.max_y is not None
            and obj.position.y > self.max_y
            or self.min_y is not None
            and obj.position.y < self.min_y
        )

    def get_message(self, obj: ObjectLike) -> str:
        if self.max_x is not None and obj.position.x > self.max_x:
            return f"{obj.name} x point of {obj.position.x} is more than its safe maximum of {self.max_x}."
        if self.min_x is not None and obj.position.x < self.min_x:
            return f"{obj.name} x point of {obj.position.x} is less than its safe minimum of {self.min_x}."
        if self.max_y is not None and obj.position.y > self.max_y:
            return f"{obj.name} y point of {obj.position.y} is more than its safe maximum of {self.max_y}."
        if self.min_y is not None and obj.position.y < self.min_y:
            return f"{obj.name} x point of {obj.position.y} is less than its safe maximum of {self.min_y}."
        raise NotImplementedError


class PydanticInvalidPositionWarning(PydanticWarning):
    """
    A JSON model of a warning that checks for an object being in a positional range.
    """

    max_x: int | None = None
    min_x: int | None = None
    max_y: int | None = None
    min_y: int | None = None
