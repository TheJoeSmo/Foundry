from typing import Protocol

from attr import attrs


class SizeProtocol(Protocol):
    """
    A two dimensional representation of a size of a given object.

    Attributes
    ----------
    width: int
        The width of the object being represented.
    height: int
        The height of the object being represented.
    """

    width: int
    height: int


@attrs(slots=True, auto_attribs=True)
class Size:
    """
    A two dimensional representation of a size, that uses ``attrs`` to create a basic
    implementation.

    Attributes
    ----------
    width: int
        The width of the object being represented.
    height: int
        The height of the object being represented.
    """

    width: int
    height: int
