from typing import Generic, Type, TypeVar

from pydantic import BaseModel, validator

from foundry.core.namespace.Namespace import Namespace
from foundry.core.namespace.Path import Path, is_valid_name

_T = TypeVar("_T")


class NamespaceElement(BaseModel, Generic[_T]):
    """
    Validates a referenced element inside of a namespace to ensure that it exists and is of the correct
    type.

    Attributes
    ----------
    parent: Namespace[_T]
        The namespace which the element of key `name` should exist inside.
    name: str
        The index or key associated inside `parent` of the element.
    type_: Type[_T]
        The type the element should take.

    Raises
    ------
    ValueError
        If the name is not a valid name for an element.
    ValueError
        If there does not exist an element inside `parent` at `name`.
    ValueError
        If the element inside `parent` at `name` is not of `type_`.
    """

    parent: Namespace[_T]
    name: str
    type_: Type[_T]

    class Config:
        arbitrary_types_allowed = True  # Allow the use of a namespace.

    @validator("name", pre=True)
    def validate_valid_name(cls, name: str) -> str:
        """
        Validates that the name could be referenced inside any namespace.

        Parameters
        ----------
        name : str
            The name to validate.

        Returns
        -------
        str
            The validated name.

        Raises
        ------
        ValueError
            If the name could not be referenced inside any namespace.
        """
        if not is_valid_name(name):
            raise ValueError(f"Invalid element name `{name}`")
        return name

    @validator("name")
    def validate_name_is_in_namespace(cls, name: str, values: dict) -> str:
        """
        Validates that `name` exists inside `parent`.

        Parameters
        ----------
        name : str
            The name to validate.
        values : dict
            The values already validated, namely `namespace`.

        Returns
        -------
        str
            The validated name.

        Raises
        ------
        ValueError
            If there does not exist an element at `name` inside `parent`.
        """
        namespace: Namespace[_T] = values["parent"]
        if name not in namespace:
            raise ValueError(f"'{name}' does not exist at {Path(tuple(namespace.path))!s}")
        return name

    @validator("type_")
    def validate_element_to_type(cls, type_: Type[_T], values: dict) -> Type[_T]:
        """
        Validates that the element is of `type_`.

        Parameters
        ----------
        type_ : Type[_T]
            The expected type of the element.
        values : dict
            The values already validated, namely `parent` and `name`.

        Returns
        -------
        Type[_T]
            The type used to validate the element.

        Raises
        ------
        ValueError
            The element was not of `type_`.
        """
        namespace: Namespace[_T] = values["parent"]
        if "name" in values and values["name"] in namespace:  # Only check if input is valid.
            obj = namespace[values["name"]]
            if not isinstance(obj, type_):
                raise ValueError(
                    f"Object `{obj}` at {Path(tuple(namespace.path))!s}.{values['name']} "
                    + f"is not a {type_.__name__}, but a {obj.__class__.__name__}"
                )
        return type_

    @property
    def element(self) -> _T:
        """
        Provides the element indexed at `name` inside `parent`.

        Returns
        -------
        _T
            The element indexed inside `parent` with a key of `name`.
        """
        return self.parent[self.name]
