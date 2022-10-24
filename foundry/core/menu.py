from attr import attrs

from foundry.core.icon import Icon
from foundry.core.namespace import (
    ConcreteValidator,
    KeywordValidator,
    OptionalValidator,
    StringValidator,
    default_validator,
    validate,
)


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
@default_validator
class MenuOption(ConcreteValidator, KeywordValidator):
    text: str | None = None
    icon: Icon | None = None
    help_text: str | None = None

    @classmethod
    @validate(
        text=OptionalValidator.generate_class(StringValidator),
        icon=OptionalValidator.generate_class(Icon),
        help_text=OptionalValidator.generate_class(StringValidator),
    )
    def validate(cls, text: str | None, icon: Icon | None, help_text: str | None):
        return cls(text, icon, help_text)
