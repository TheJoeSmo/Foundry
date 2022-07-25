from __future__ import annotations

from os import name
from pathlib import Path, _PosixFlavour, _WindowsFlavour  # type: ignore
from typing import Type, TypeVar

from pydantic.errors import PathNotAFileError
from pydantic.validators import path_exists_validator, path_validator

from foundry import root_dir
from foundry.core.namespace import ConcreteValidator, MetaValidator, TypeHandler

_FP = TypeVar("_FP", bound="FilePath")


class FilePath(Path, ConcreteValidator):
    __slots__ = ()

    __type_default__ = "DEFAULT"
    __names__ = ("file", "File", "FILE", "file path", "FilePath", "FILE PATH", "FILE_PATH")

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

    @staticmethod
    def validate_from_file(v: dict) -> FilePath:
        path = FilePath.get_default_argument(v)
        if not isinstance(path, str):
            raise ValueError(f"{path} is not a string")
        if path.startswith("$"):
            path = root_dir / path[1:]

        for validator in FilePath.__get_validators__():
            path = validator(path)  # type: ignore
        return FilePath(path)


def _validate_file(class_: Type[_FP], v) -> _FP:
    return class_(class_.validate_from_file(v))


FilePath.__validator_handler__ = TypeHandler({"DEFAULT": MetaValidator(_validate_file, use_parent=False)})
