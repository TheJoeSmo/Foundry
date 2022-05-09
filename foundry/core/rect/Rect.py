from __future__ import annotations

from attr import attrs
from pydantic.errors import MissingError

from foundry.core.point.Point import Point
from foundry.core.size.Size import Size


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class Rect:
    """
    A two dimensional representation of a box, that uses ``attrs`` to create a basic
    implementation.

    Attributes
    ----------
    point: Point
        The upper left corner of the rect.
    size: Size
        The size of the box.
    """

    point: Point
    size: Size

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, values) -> Rect:
        if "point" not in values:
            MissingError()
        if "size" not in values:
            MissingError()
        return Rect(Point.validate(values["point"]), Size.validate(values["size"]))
