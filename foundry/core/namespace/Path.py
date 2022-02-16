from __future__ import annotations

from collections.abc import Iterator
from re import search
from typing import Any, Optional, Union

from attr import attrs, field, validators


class InvalidChildName(ValueError):
    """
    An exception raised when a child's name inside :class:~`foundry.core.namespace.util.ChildTreeProtocol` is
    considered to be invalid.

    Attributes
    ----------
    name: str
        The invalid string in its entirety.
    invalid_element: str
        The invalid portion of the string.  By definition this must be a subset of name.
    """

    __slots__ = "name", "invalid_element"

    name: str
    invalid_element: Optional[str]

    def __init__(self, name: str, invalid_element: Optional[str] = None):
        self.name = name
        self.invalid_element = invalid_element
        if invalid_element is not None:
            super().__init__(f'The name "{name}" contained an invalid element: {invalid_element}.')
        else:
            super().__init__(f'The name "{name}" contained an invalid element.')


def is_valid_name(name: Any, *, regrex: str = "^[A-Za-z_][A-Za-z0-9_]*$") -> bool:
    """
    Determines if a name for a given child is considered valid.

    Parameters
    ----------
    name : Any
        The name to check if it is valid.
    regrex : str, optional
        The regrex expression to check for validity, by default "^[A-Za-z_][A-Za-z0-9_]+$"

    Returns
    -------
    bool
        If the name is valid.
    """
    return bool(search(regrex, name)) if isinstance(name, str) else False


def _is_valid_list_of_names(inst, attr, value: tuple) -> tuple[str, ...]:
    for name in value:
        if not is_valid_name(name):
            raise InvalidChildName(name)
    return value


@attrs(slots=True, auto_attribs=True, frozen=True, hash=True, eq=True)
class Path:
    """
    A representation of a path that be taken through a tree structure to get to a given element.

    Attributes
    ----------
    decomposed_path: tuple[str, ...] = (,)
        A series of strings that represent a series of keys that can be taken to traverse a tree structure.

    Raises
    ------
    InvalidChildName
        If any of the children name are returned as invalid for :func:`foundry.core.namespace.Path.is_valid_name`.
    """

    decomposed_path: tuple[str, ...] = field(
        factory=tuple, validator=[validators.instance_of(tuple), _is_valid_list_of_names]
    )

    def __str__(self) -> str:
        return ".".join(self.decomposed_path)

    def __iter__(self) -> Iterator[str]:
        return iter(self.decomposed_path)

    def __getitem__(self, key: Union[int, slice]):
        return self.decomposed_path.__getitem__(key)

    @property
    def root(self) -> str:
        """
        Provides the root of the element referenced.

        Returns
        -------
        str
            The root of the element referenced.
        """
        return "" if len(self.decomposed_path) == 0 else self.decomposed_path[0]

    @property
    def parent(self) -> Optional[Path]:
        """
        Provides the parent Path of this path, if one exists.

        Returns
        -------
        Optional[Path]
            The parent path of this path if one exists, else None.
        """
        return None if len(self.decomposed_path) == 0 else Path(self.decomposed_path[:-1])

    @property
    def name(self) -> str:
        """
        Provides the name of the element referenced.

        Returns
        -------
        str
            The name of the element referenced.
        """
        return "" if len(self.decomposed_path) == 0 else self.decomposed_path[-1]

    def create_child(self, name: str) -> Path:
        """
        Creates a child element with this instance as the parent and name as a child of parent.

        Parameters
        ----------
        name : str
            A child of this path to create a new instance from.

        Returns
        -------
        Path
            A path that represents a child of this parent with the name as the top element.

        Raises
        ------
        InvalidChildName
            If name is returned as invalid for :func:`foundry.core.namespace.Path.is_valid_name`.
        """
        return self.__class__(tuple(list(self.decomposed_path) + [name]))

    @classmethod
    def create_child_from_parent(cls, parent: Optional[Path], child: str) -> Path:
        """
        Create a child of the same instance of this from parent, if it exists, and a child.  If no child exists, then
        the child will be created as root.

        Parameters
        ----------
        parent : Optional[Path]
            A parent that may exist to create a child from.
        child : str
            The name of the top most name to exist inside the path.

        Returns
        -------
        Self
            A path that represents a child of the parent, if it exists, otherwise root.

        Raises
        ------
        InvalidChildName
            If name is returned as invalid for :func:`foundry.core.namespace.Path.is_valid_name`.
        """
        return cls((child,)) if parent is None else parent.create_child(child)

    @classmethod
    def from_string(cls, s: str) -> Path:
        """
        Creates a path from a string.

        Parameters
        ----------
        s : str
            The string to convert to a path.

        Returns
        -------
        Self
            A path that represents a path.

        Raises
        ------
        InvalidChildName
            If any of the children name are returned as invalid for :func:`foundry.core.namespace.Path.is_valid_name`.
        """
        return cls(tuple(s.split("."))) if s else cls()
