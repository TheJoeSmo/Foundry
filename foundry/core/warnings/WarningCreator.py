from pydantic import BaseModel

from foundry.core.warnings.util import type_to_pydantic_warning
from foundry.core.warnings.Warning import PydanticWarning
from foundry.core.warnings.WarningType import WarningType


class WarningCreator(BaseModel):
    def __init_subclass__(cls, **kwargs) -> None:
        return super().__init_subclass__(**kwargs)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def generate_warning(cls, v: dict) -> PydanticWarning:
        """
        The constructor for each specific warning.

        Parameters
        ----------
        v : dict
            The dictionary to create the warning.

        Returns
        -------
        Warning
            The created warning as defined by `v["type"]`

        Raises
        ------
        NotImplementedError
            If the constructor does not have a valid constructor for `v["type"]`.
        """
        type_ = WarningType(v["type"])
        warnings = type_to_pydantic_warning()
        if type_ not in warnings:
            raise NotImplementedError(f"There is no layout of type {type_}")

        return warnings[type_](**v)

    @classmethod
    def validate(cls, v):
        if not isinstance(v, dict):
            raise TypeError("Dictionary required")
        if "type" not in v:
            raise TypeError("Must have a type")
        if not WarningType.has_value(type_ := v["type"]):
            raise TypeError(f"{type_} is not a valid warning type")
        return cls.generate_warning(v)
