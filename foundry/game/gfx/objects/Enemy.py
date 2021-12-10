from typing import Protocol

from attr import attrs

from foundry.core.Position import Position, PositionProtocol


class EnemyProtocol(Protocol):
    """
    A representation of an enemy inside a level.

    Attributes
    ----------
    type: int
        The type of enemy
    position: PositionProtocol
        The position of the enemy
    """

    type: int
    position: PositionProtocol

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
    position: PositionProtocol
        The position of the enemy
    """

    type: int
    position: PositionProtocol

    def __bytes__(self) -> bytes:
        return bytes([self.type, self.position.x, self.position.y])

    @classmethod
    def from_bytes(cls, data: bytes):
        return cls(data[0], Position(data[1], data[2]))
