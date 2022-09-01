from __future__ import annotations

from os import name
from pathlib import Path, _PosixFlavour, _WindowsFlavour  # type: ignore

from pydantic.errors import PathNotAFileError
from pydantic.validators import path_exists_validator, path_validator

from foundry import root_dir
from foundry.core.namespace import (
    ConcreteValidator,
    SingleArgumentValidator,
    default_validator,
)


@default_validator(use_parent=False, method_name="validate_from_file")
class FilePath(Path, ConcreteValidator, SingleArgumentValidator):
    __names__ = ("__FILE__", "file", "File", "FILE", "file path", "FilePath", "FILE PATH", "FILE_PATH")
    __slots__ = ()

    # Path won't work unless we set this magical undocumented variable, so we set it.
    _flavour = _PosixFlavour() if name == "posix" else _WindowsFlavour()

    @classmethod
    def __get_validators__(cls):
        # Copied directly from Pydantic's FilePath version which didn't work...
        yield path_validator
        yield path_exists_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: Path, **kwargs) -> Path:
        # Copied directly from Pydantic's FilePath version which didn't work...
        if not value.is_file():
            raise PathNotAFileError(path=value)

        return value

    @classmethod
    def validate_from_file(cls, v: dict) -> FilePath:
        path = cls.get_default_argument(v)
        if not isinstance(path, str):
            raise ValueError(f"{path} is not a string")
        if path.startswith("$"):
            path = root_dir / path[1:]

        for validator in cls.__get_validators__():
            path = validator(path)  # type: ignore
        return cls(path)
