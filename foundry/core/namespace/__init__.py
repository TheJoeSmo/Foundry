from enum import Enum


class NamespaceType(str, Enum):
    """
    The type of elements allowed inside the namespace.
    """

    NONE = "NONE"
    INTEGER = "INTEGER"
    STRING = "STRING"
    FLOAT = "FLOAT"
    FILE = "FILE"
    DRAWABLE = "DRAWABLE"

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


class Uninitializable:
    """
    A class that will always throw an exception on initialization.  Used to enforce no elements for a given
    namespace.
    """

    def __init__(self, parent, *args, **kwargs):
        raise ValueError(f"{parent!s} contains no elements")
