from attr import attrs

from foundry.core.warnings.Warning import PydanticWarning, Warning
from foundry.game.gfx.objects.LevelObject import LevelObject


@attrs(slots=True, frozen=True, auto_attribs=True)
class InvalidSizeWarning(Warning):
    """
    A warning for an object exceeding its valid size range.
    """

    max_width: int | None = None
    min_width: int | None = None
    max_height: int | None = None
    min_height: int | None = None

    def check_object(self, obj: LevelObject, *args, **kwargs) -> bool:
        """
        Determines if the object should emit a warning for having an invalid size.

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
            self.max_width is not None
            and obj.rendered_size.width > self.max_width
            or self.min_width is not None
            and obj.rendered_size.width < self.min_width
            or self.max_height is not None
            and obj.rendered_size.height > self.max_height
            or self.min_height is not None
            and obj.rendered_size.height < self.min_height
        )

    def get_message(self, obj: LevelObject) -> str:
        if self.max_width is not None and obj.rendered_size.width > self.max_width:
            return f"{obj.name} width of {obj.rendered_size.width} is more than its safe maximum of {self.max_width}."
        if self.min_width is not None and obj.rendered_size.width < self.min_width:
            return f"{obj.name} width of {obj.rendered_size.width} is less than its safe minimum of {self.min_width}."
        if self.max_height is not None and obj.rendered_size.height > self.max_height:
            return (
                f"{obj.name} height of {obj.rendered_size.height} is more than its safe maximum of {self.max_height}."
            )
        if self.min_height is not None and obj.rendered_size.height < self.min_height:
            return (
                f"{obj.name} height of {obj.rendered_size.height} is less than its safe maximum of {self.min_height}."
            )
        raise NotImplementedError


class PydanticInvalidSizeWarning(PydanticWarning):
    """
    A JSON model of a warning that checks for an object being in a size range.
    """

    max_width: int | None = None
    min_width: int | None = None
    max_height: int | None = None
    min_height: int | None = None
