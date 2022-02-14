from pydantic import BaseModel

from foundry.core.drawable.Drawable import Drawable
from foundry.core.drawable.DrawableGenerator import DrawableGeneratator
from foundry.core.warnings.Warning import Warning
from foundry.core.warnings.WarningCreator import WarningCreator


class Definition(BaseModel):
    description: str = ""
    warnings: list[WarningCreator] = []
    overlays: list[DrawableGeneratator] = []

    def get_warnings(self) -> list[Warning]:
        return self.warnings.copy()  # type: ignore

    def get_overlays(self) -> list[Drawable]:
        return self.overlays.copy()  # type: ignore

    class Config:
        use_enum_values = True
