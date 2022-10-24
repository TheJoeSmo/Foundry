from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon

from foundry.core.file import FilePath
from foundry.core.namespace import (
    ConcreteValidator,
    KeywordValidator,
    default_validator,
    validate,
)


@default_validator
class Icon(QIcon, ConcreteValidator, KeywordValidator):
    """
    An extension of `QIcon` to provide Pydantic compatibility and integration with the namespace API.
    """

    __names__ = ("__ICON_VALIDATOR__", "icon", "Icon", "ICON")
    __required_validators__ = (FilePath,)

    @classmethod
    @validate(path=FilePath)
    def validate(cls, path: Path):
        return cls(str(path))
