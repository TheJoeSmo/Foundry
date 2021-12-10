from attr import attrs
from pydantic import BaseModel

from foundry.core.warnings.WarningType import WarningType


@attrs(slots=True, frozen=True, auto_attribs=True)
class Warning:
    """
    A generic dataclass to represent a given warning.
    """

    def __init__(*args, **kwargs):
        pass

    def check_object(self, obj, *args, **kwargs) -> bool:
        """
        Determines if the object should emit a warning.

        Parameters
        ----------
        obj : ObjectLike
            The object to check.

        Returns
        -------
        bool
            If the object should emit a warning.
        """
        return True

    def get_message(self, obj, *args, **kwargs) -> str:
        """
        Provides a message for an object with a warning.

        Parameters
        ----------
        obj : ObjectLike
            The object to provide a warning for.

        Returns
        -------
        str
            The warning for the object.
        """
        return "Something is wrong"


class PydanticWarning(BaseModel):
    """
    A JSON model of a generic Warning through Pydantic

    Attributes
    ----------
    type: WarningType
        The type of warning.
    """

    type: WarningType

    class Config:
        use_enum_values = True

    def to_warning(self) -> Warning:
        """
        Converts self to a warning with respect to its type.

        Returns
        -------
        Warning
            That represents self.
        """
        from foundry.core.warnings.util import convert_pydantic_to_warning

        d = self.dict().copy()
        d.pop("type")  # The type is no longer needed
        return convert_pydantic_to_warning(self)(**d)
