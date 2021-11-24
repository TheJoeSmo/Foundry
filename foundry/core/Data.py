from typing import Protocol

from attr import attrs


class DataProtocol(Protocol):
    """
    A representation of bytes inside a given file.

    Attributes
    ----------
    location: int
        The starting point of the data.
    data: bytes
        The data at that location.
    """

    location: int
    data: bytes


@attrs(slots=True, auto_attribs=True)
class Data:
    """
    A representation of bytes inside a given file, that uses ``attrs`` to create a basic implementation.

    Attributes
    ----------
    location: int
        The starting point of the data.
    data: bytes
        The data at that location.
    """

    location: int
    data: bytes
