from typing import Protocol

from attr import attrs

from foundry.core.geometry import Point


class EnemyProtocol(Protocol):
    """
    A representation of an enemy inside a level.

    Attributes
    ----------
    type: int
        The type of enemy
    point: Point
        The point of the enemy
    """

    type: int
    point: Point

    def __bytes__(self) -> bytes:
        ...

    @classmethod
    def from_bytes(cls, data: bytes):
        ...


@attrs(slots=True, auto_attribs=True)
class Enemy:
    """
    A representation of an enemy inside a level, that uses ``attrs`` to create a basic implementation.

    Attributes
    ----------
    type: int
        The type of enemy
    point: Point
        The point of the enemy
    """

    type: int
    point: Point

    def __bytes__(self) -> bytes:
        return bytes([self.type, self.point.x, self.point.y])

    @classmethod
    def from_bytes(cls, data: bytes):
        return cls(data[0], Point(data[1], data[2]))
