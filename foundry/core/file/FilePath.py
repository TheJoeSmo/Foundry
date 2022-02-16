from __future__ import annotations

from os import name
from pathlib import Path, _PosixFlavour, _WindowsFlavour

from pydantic.errors import PathNotAFileError
from pydantic.validators import path_exists_validator, path_validator


class FilePath(Path):
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
