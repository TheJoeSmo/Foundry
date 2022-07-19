from pydantic import BaseModel

from foundry import root_dir
from foundry.core.file import FileType
from foundry.core.file.FilePath import FilePath
from foundry.core.namespace import Namespace, Path, validate_element


class FileFromNamespace(BaseModel):
    parent: Namespace
    path: str
    name: str

    class Config:
        arbitrary_types_allowed = True  # Allow the use of a namespace.

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: dict) -> FilePath:
        parent: Namespace = v.get("parent", None)
        if parent is None:
            raise ValueError("Parent was not provided")
        if "path" not in v:
            raise ValueError("Path is not defined")
        path: str = v["path"]
        if "name" not in v:
            raise ValueError("Name is not defined")
        name: str = v["name"]

        return validate_element(
            parent=parent.from_path(Path.validate(parent=parent, path=path)), name=name, type=FilePath
        )


def validate_from_file(v: dict) -> FilePath:
    if "path" not in v:
        raise ValueError("No path is present")
    path = v["path"]
    if not isinstance(path, str):
        raise ValueError(f"{path} is not a string")
    if path.startswith("$"):
        path = root_dir / path[1:]
    return FilePath(path)


class FileGenerator(BaseModel):
    type: FileType

    class Config:
        use_enum_values = True

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def generate_file_path(cls, v: dict) -> FilePath:
        """
        The constructor for each specific file path.

        Parameters
        ----------
        v : dict
            The dictionary to create the file path.

        Returns
        -------
        FilePath
            The created file path as defined by `v["type"]`.

        Raises
        ------
        NotImplementedError
            If the constructor does not have a valid constructor for `v["type"]`.
        """
        type_ = FileType(v["type"])
        if type_ == FileType.FROM_FILE:
            return validate_from_file(v)
        elif type_ == FileType.FROM_NAMESPACE:
            return FileFromNamespace.validate(v)
        raise NotImplementedError(f"There is no file path of type {type_}")

    @classmethod
    def validate(cls, v: dict) -> FilePath:
        """
        Validates that the provided object is a valid FilePath.

        Parameters
        ----------
        v : dict
            The dictionary to create the file path.

        Returns
        -------
        FilePath
            If validated, a file path will be created in accordance to `generate_file_path`.

        Raises
        ------
        TypeError
            If a dictionary is not provided.
        TypeError
            If the dictionary does not contain the key `"type"`.
        TypeError
            If the type provided is not inside :class:`~foundry.core.file.FileType`.
        """
        if not isinstance(v, dict):
            raise TypeError("Dictionary required")
        if "type" not in v:
            raise TypeError("Must have a type")
        if not FileType.has_value(type_ := v["type"]):
            raise TypeError(f"{type_} is not a valid file type")
        return cls.generate_file_path(v)
