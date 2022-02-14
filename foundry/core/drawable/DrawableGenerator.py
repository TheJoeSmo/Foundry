from pydantic import BaseModel

from foundry.core.drawable import DrawableType
from foundry.core.drawable.BlockGroupDrawable import PydanticBlockGroupDrawable
from foundry.core.drawable.Drawable import Drawable


class DrawableGeneratator(BaseModel):
    def __init_subclass__(cls, **kwargs) -> None:
        return super().__init_subclass__(**kwargs)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def generate_drawable(cls, v: dict) -> Drawable:
        """
        The constructor for each specific drawable.

        Parameters
        ----------
        v : dict
            The dictionary to create the drawable.

        Returns
        -------
        Drawable
            The created drawable as defined by `v["type"]`.

        Raises
        ------
        NotImplementedError
            If the constructor does not have a valid constructor for `v["type"]`.
        """
        type_ = DrawableType(v["type"])
        if type_ == DrawableType.BLOCK_GROUP:
            return PydanticBlockGroupDrawable(**v)
        raise NotImplementedError(f"There is no drawable of type {type_}")

    @classmethod
    def validate(cls, v: dict) -> Drawable:
        """
        Validates that the provided object is a valid Drawable.

        Parameters
        ----------
        v : dict
            The dictionary to create the drawable.

        Returns
        -------
        Drawable
            If validated, a drawable will be created in accordance to `generate_drawable`.

        Raises
        ------
        TypeError
            If a dictionary is not provided.
        TypeError
            If the dictionary does not contain the key `"type"`.
        TypeError
            If the type provided is not inside :class:`~foundry.core.drawable.Drawable.DrawableType`.
        """
        if not isinstance(v, dict):
            raise TypeError("Dictionary required")
        if "type" not in v:
            raise TypeError("Must have a type")
        if not DrawableType.has_value(type_ := v["type"]):
            raise TypeError(f"{type_} is not a valid widget type")
        return cls.generate_drawable(v)
