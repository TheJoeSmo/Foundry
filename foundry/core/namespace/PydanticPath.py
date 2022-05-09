from typing import Optional

from pydantic import BaseModel, validator

from foundry.core.namespace.Namespace import Namespace
from foundry.core.namespace.Path import Path, is_valid_name


class PydanticPath(BaseModel):
    """
    A validator to ensure a path is valid.  The path can be independent or dependent on a parent:
    If a path is dependent on a parent, then both a parent must exist and the path must exist relative
    to the parent and path.

    Attributes
    ----------
    use_parent: bool = True
        If the path depends on a parent, by default True.
    parent: Optional[Namespace]
        The parent, if one exists, for the path to depend on.

        If `use_parent` is true, then `parent` must exist.
    path: str
        The string to derive the true path from, relative to `parent`, if `use_parent` is True.

    Raises
    ------
    ValueError
        If `path` can be derived to a path.
    ValueError
        If `parent` is not provided and `use_parent` is True.
    ValueError
        If `use_parent` and there does not exist a :class:~`foundry.core.namespace.Namespace.Namespace`
        relative to `parent` and `path`, specified by
        :func:~`foundry.core.namespace.Namespace.Namespace.namespace_exists_at_path`.
    """

    use_parent: bool = True
    parent: Optional[Namespace] = None
    path: str

    class Config:
        arbitrary_types_allowed = True  # Allow the use of an optional namespace.

    @validator("parent", pre=True, always=True)
    def validate_parent_must_exist_if_parent_is_used(cls, parent: Optional[Namespace], values: dict):
        """
        Validates `parent` exists when `use_parent` is set.

        Parameters
        ----------
        parent : Optional[Namespace]
            The parent to validate.
        values : dict
            The values already validated, namely `use_parent`.

        Returns
        -------
        Optional[Namespace]
            The validated parent.

        Raises
        ------
        ValueError
            If `parent` is None and `use_parent` is set.
        """
        if values.get("use_parent", True) and parent is None:
            raise ValueError("Parent does not exist")
        return parent

    @validator("path")
    def validate_path_name(cls, path: str) -> str:
        """
        Validates that the path can form a :class:~`foundry.core.namespace.Path.Path`.

        Parameters
        ----------
        path : str
            The path to validate.

        Returns
        -------
        str
            The validated path.

        Raises
        ------
        ValueError
            If the path cannot form a :class:~`foundry.core.namespace.Path.Path` as specified by
        :func:~`foundry.core.namespace.Path.is_valid_name`.
        """
        if path:  # Allow for empty strings to denote the root node.
            for name in path.split("."):
                if not is_valid_name(name):
                    raise ValueError(f"Invalid path name '{name}' from `{path}`")
        return path

    @validator("path")
    def validate_path_exists(cls, s: str, values: dict) -> str:
        """
        Validates that `s` can be derived to a :class:~`foundry.core.namespace.Path.Path` is relative to
        `parent` such that a namespace exists at the path generated if `use_parent` is set.

        Parameters
        ----------
        s : str
            The string to derive a path from
        values : dict
            The values already generated, namely `use_parent` and `parent`.

        Returns
        -------
        str
            The validated string.

        Raises
        ------
        ValueError
            If `use_parent` is set and `s` does not form a path which is `parent` such that there exists
            a namespace relative to path and parent.
        """

        if values.get("use_parent", True):
            if (parent := values.get("parent", None)) is None:
                # An exception will already be raised, so just return the value and the invariant is
                # violated, thus we should not try to provide any additional verdicts.
                return s
            if not parent.namespace_exists_at_path(path := Path.from_string(s)):
                raise ValueError(f"'{path!s}' does not exist in {parent!s}")
        return s

    def to_path(self) -> Path:
        """
        Generates a path from the validated path.

        Returns
        -------
        Path
            The path that was validated.
        """
        return Path.from_string(self.path)
