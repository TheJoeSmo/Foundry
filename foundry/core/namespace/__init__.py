from foundry.core.Enum import Enum


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


class Uninitializable:
    """
    A class that will always throw an exception on initialization.  Used to enforce no elements for a given
    namespace.
    """

    def __init__(self, parent, *args, **kwargs):
        raise ValueError(f"{parent!s} contains no elements")
