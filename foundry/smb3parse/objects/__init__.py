"""
Describes all objects, that are part of a level, i. e. platforms, enemies, items, jumps, auto scroll objects etc.
"""
from abc import ABC
from typing import Optional, Protocol

import attr

from foundry.core.Position import Position, PositionProtocol

MIN_DOMAIN = 0
MAX_DOMAIN = 7
MIN_Y_VALUE = 0
MAX_Y_VALUE = 27
MIN_ID_VALUE = 0
MAX_ID_VALUE = 0xFF
MIN_X_VALUE = 0
MAX_X_VALUE = 0xFF
MIN_ADDITIONAL_LENGTH = 0
MAX_ADDITIONAL_LENGTH = 0xFF

MAX_ENEMY_ITEM_ID = 0xEC


class LevelComponentProtocol(Protocol):
    """
    An outline of any object that composes an element inside the game.

    Attributes
    ----------
    domain: int
        The domain or set of component that the component is housed inside.
    index: int
        The specific byte of data that determines a limited amount of information with regard to
        the component.
    position: int
        The location inside the level that the component is housed.
    """

    domain: int
    index: int
    position: PositionProtocol


def domain_check(instance, attribute, value):
    """
    A check to ensure that the domain of a given object is between 0 and 7.

    Raises
    ------
    TypeError
        Will be raised if the domain is not an integer.
    ValueError
        Will be raised if the domain is not between 0 and 7.
    """
    if not isinstance(value, int):
        raise TypeError(f"{instance.__class__.__name__} only supports integers inside the domain, not {type(value)}")
    if 0 > value < 7:
        raise ValueError(f"{instance.__class__.__name__} only supports domains from 0 to 7, not {value}")


def index_check(instance, attribute, value):
    """
    A check to ensure that the index of a given object is between 0 and 255.

    Raises
    ------
    TypeError
        Will be raised if the index is not an integer.
    ValueError
        Will be raised if the index is not between 0 and 255.
    """
    if not isinstance(value, int):
        raise TypeError(f"{instance.__class__.__name__} only supports integers inside the index, not {type(value)}")
    if 0 > value < 0xFF:
        raise ValueError(f"{instance.__class__.__name__} only supports index from 0 to 255, not {value}")


def position_check(instance, attribute, value):
    """
    A check to ensure that the position of a given object has an x and y
    that are between 0 and 255.

    Raises
    ------
    ValueError
        Will be raised if either the x or y is not between 0 and 255.
    AttributeError
        Will be raised if the position does not contain a field for x or y.
    """
    try:
        if 0 > value.x < 0xFF:
            raise ValueError(f"{instance.__class__.__name__} only supports x from 0 to 255, not {value.x}")
    except AttributeError:
        raise AttributeError(f"{value.__class__.__name__} does not contain the field x")
    try:
        if 0 > value.y < 27:
            raise ValueError(f"{instance.__class__.__name__} only supports y from 0 to 27, not {value.y}")
    except AttributeError:
        raise AttributeError(f"{value.__class__.__name__} does not contain the field y")


@attr.s(slots=True)
class LevelComponent:
    """
    A basic implementation of `~foundry.smb3parse.objects.LevelComponentProtocol`.

    Attributes
    ----------
    domain: int
        The domain or set of component that the component is housed inside.
        Must be between 0 and 7.
    index: int
        The specific byte of data that determines a limited amount of information with regard to
        the component.
        Must be between 0 and 255.
    position: int
        The location inside the level that the component is housed.
        Both x and y must be between 0 and 255.
    """

    domain: int = attr.ib(validator=domain_check, default=0)
    index: int = attr.ib(validator=index_check, default=0)
    position: Position = attr.ib(validator=position_check, default=attr.Factory(lambda: Position(0, 0)))


class InLevelObject(ABC):
    """
    Describes objects that are positioned at a specific place in a level and have some sort of representation, be it
    visible like platforms and enemies or invisible, like auto scroll items or jumps.
    """

    def __init__(self, data: bytearray):
        self._data: bytearray = data
        self.level_component = LevelComponent()
        self._length: Optional[int] = None

    @property
    def id(self):
        return self.level_component.index

    @id.setter
    def id(self, value):
        self.level_component.index = value

    @property
    def domain(self):
        return self.level_component.domain

    @domain.setter
    def domain(self, value):
        self.level_component.domain = value

    @property
    def x(self):
        return self.level_component.position.x

    @x.setter
    def x(self, value):
        self.level_component.position.x = value

    @property
    def y(self):
        return self.level_component.position.y

    @y.setter
    def y(self, value):
        self.level_component.position.y = value

    @property
    def additional_length(self):
        return self._length

    @additional_length.setter
    def additional_length(self, value):
        self._length = value

    @property
    def has_additional_length(self):
        return self.additional_length is not None
