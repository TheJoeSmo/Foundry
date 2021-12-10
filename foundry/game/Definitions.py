from pydantic import BaseModel

from foundry.core.warnings.Warning import Warning
from foundry.core.warnings.WarningCreator import WarningCreator


class Definition(BaseModel):
    description: str = ""
    warnings: list[WarningCreator] = []

    def get_warnings(self) -> list[Warning]:
        return self.warnings.copy()  # type: ignore

    class Config:
        use_enum_values = True
