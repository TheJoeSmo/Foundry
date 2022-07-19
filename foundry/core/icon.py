from __future__ import annotations

from enum import Enum

from PySide6.QtGui import QIcon

from foundry.core.file.FileGenerator import FileGenerator
from foundry.core.namespace import Namespace, Path, validate_element


class IconType(str, Enum):
    """
    The type of icon to be applied.
    """

    FROM_FILE = "FROM FILE"
    FROM_NAMESPACE = "FROM NAMESPACE"

    @classmethod
    def has_value(cls, value: str) -> bool:
        """
        A convenience method to quickly determine if a value is a valid enumeration.

        Parameters
        ----------
        value : str
            The value to check against the enumeration.

        Returns
        -------
        bool
            If the value is inside the enumeration.
        """
        return value in cls._value2member_map_


class Icon(QIcon):
    """
    An extension of `QIcon` to provide Pydantic compatibility and integration with the namespace API.
    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate_from_file(cls, *_, parent: Namespace, file: dict[str, str], **kwargs):
        """
        Generates and validates an icon from a file.

        Parameters
        ----------
        parent : Namespace
            The parent namespace of the icon, which may be used to generate a file path.
        file : dict[str, str]
            The data required to generate the file.

        Returns
        -------
        Self
            The icon generated from the file provided.
        """
        return Icon(str(FileGenerator.validate(file | {"parent": parent})))

    @classmethod
    def validate_from_namespace(cls, *_, parent: Namespace, name: str, path: str, **kwargs):
        """
        Generates and validates an icon from another existing icon from `parent`.

        Parameters
        ----------
        parent : Namespace
            The namespace with the icon to copy.
        name : str
            The name of the icon.
        path : str
            The path to the icon Namespace.

        Returns
        -------
        Self
            The icon inside the Namespace.
        """
        return validate_element(parent=parent.from_path(Path.validate(parent=parent, path=path)), name=name, type=cls)

    @classmethod
    def generate_icon(cls, v: dict):
        """
        The constructor for each specific icon.

        Parameters
        ----------
        v : dict
            The dictionary to create the icon.

        Returns
        -------
        Self
            The created icon as defined by `v["type"]`.

        Raises
        ------
        NotImplementedError
            If the constructor does not have a valid constructor for `v["type"]`.
        """
        type_ = IconType(v["type"])
        if type_ == IconType.FROM_FILE:
            return cls.validate_from_file(**v)
        elif type_ == IconType.FROM_NAMESPACE:
            return cls.validate_from_namespace(**v)
        raise NotImplementedError(f"There is no file path of type {type_}")

    @classmethod
    def validate(cls, v: dict[str, str]):
        """
        Validates that the provided object is a valid Icon.

        Parameters
        ----------
        v : dict
            The dictionary to create the icon.

        Returns
        -------
        Icon
            If validated, an icon will be created in accordance to `generate_icon`.

        Raises
        ------
        TypeError
            If a dictionary is not provided.
        TypeError
            If the dictionary does not contain the key `"type"`.
        TypeError
            If the type provided is not inside :class:~`foundry.core.icon.IconType`_.
        """
        if not isinstance(v, dict):
            raise TypeError("Dictionary required")
        if "type" not in v:
            raise TypeError("Must have a type")
        if not IconType.has_value(type_ := v["type"]):
            raise TypeError(f"{type_} is not a valid icon type")
        return cls.generate_icon(v)
