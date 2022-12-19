from __future__ import annotations

import contextlib
from collections.abc import Mapping, MutableSequence, Sequence
from enum import Enum, auto
from reprlib import recursive_repr
from typing import Any, Generic, TypeVar

from attr import attrs

_CMV = TypeVar("_CMV", bound="ChainMapView")
_T = TypeVar("_T")


class EndianType(Enum):
    LITTLE = auto()
    BIG = auto()


class Endian:
    def endian(self, index: int, endian: EndianType = EndianType.LITTLE, size: int = 2, *args) -> int:
        raise NotImplementedError

    @classmethod
    def from_endian(cls, value: int, endian: EndianType = EndianType.LITTLE, size: int = 2, *args) -> bytes:
        """
        Generates a series of bytes associated with an integer of a specific endian type.

        Parameters
        ----------
        value : int
            The value of the integer to be converted.
        endian : EndianType, optional
            The endian type for the integer to be converted to, by default EndianType.LITTLE
        size : int, optional
            The amount of space the integer requires, by default 2

        Returns
        -------
        bytes
            The bytes associated with the converted integer of a specific endian.

        Raises
        ------
        NotImplementedError
            If an invalid EndianType is provided.
        """
        if endian == EndianType.LITTLE:
            print("auto", list(int(a) for a in value.to_bytes(size, "little")))
            return value.to_bytes(size, "little")
        elif endian == EndianType.BIG:
            return value.to_bytes(size, "big")
        raise NotImplementedError


class Findable(Generic[_T]):
    def find(self, value: _T | Sequence[_T], offset: int = 0) -> int:
        raise NotImplementedError


class FindableSequence(Sequence[_T], Findable[_T]):
    pass


class FindableEndianSequence(Sequence[_T], Findable[_T], Endian):
    pass


class FindableMutableSequence(MutableSequence[_T], FindableSequence[_T]):
    pass


class FindableEndianMutableSequence(FindableMutableSequence[_T], FindableEndianSequence[_T], Endian):
    pass


@attrs(slots=True, auto_attribs=True, init=False, frozen=True, hash=False)
class ChainMap(Mapping):
    """
    A ChainMap groups multiple dicts (or other mappings) together
    to create a single, updatable view.

    Attributes
    ----------
    The underlying mappings are stored in a tuple.  That tuple is public and can
    be accessed or updated using the *maps* attribute.  There is no other
    state.

    Notes
    -----
    Lookups search the underlying mappings successively until a key is found.

    This is derived from the original collections ChainMap, but abbreviated to
    use attrs and be frozen.
    """

    maps: tuple[Mapping]

    def __init__(self, *maps: Mapping):
        object.__setattr__(self, "maps", maps)  # get around the frozen attribute.

    def __missing__(self, key):
        raise KeyError(key)

    def __getitem__(self, key):
        for mapping in self.maps:
            with contextlib.suppress(KeyError):
                return mapping[key]  # can't use 'key in mapping' with defaultdict
        return self.__missing__(key)  # support subclasses that define __missing__

    def get(self, key, default=None):
        return self[key] if key in self else default

    def __len__(self):
        return len(set().union(*self.maps))  # reuses stored hash values if possible

    def __iter__(self):
        d = {}
        for mapping in reversed(self.maps):
            d |= dict.fromkeys(mapping)
        return iter(d)

    def __contains__(self, key):
        return any(key in m for m in self.maps)

    def __bool__(self):
        return any(self.maps)

    @recursive_repr()
    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(map(repr, self.maps))})"

    @classmethod
    def fromkeys(cls, iterable, *args):
        """
        Create a ChainMap with a single dict created from the iterable.
        """
        return cls(dict.fromkeys(iterable, *args))

    def new_child(self, m: dict | None = None, **kwargs):
        """
        New ChainMap with a new map followed by all previous maps.

        Notes
        -----
        If no map is provided, this instance will be returned.
        """
        if m is None and not kwargs:
            return self
        if m is None:
            m = kwargs
        elif kwargs:
            m.update(kwargs)
        return self.__class__(m, *self.maps)

    @property
    def parents(self):  # like Django's Context.pop()
        """
        New ChainMap from maps[1:].
        """
        return self.__class__(*self.maps[1:])

    def __or__(self, other):
        return self.__class__(self, other) if isinstance(other, Mapping) else NotImplemented

    def __ror__(self, other):
        return self.__class__(other, self) if isinstance(other, Mapping) else NotImplemented


@attrs(slots=True, auto_attribs=True, init=False, frozen=True, hash=False)
class ChainMapView(Mapping):
    """
    A view of a chain map, used to limit the values able to be acquired.

    Attributes
    ----------
    chain_map: ChainMap | ChainMapView
        The underlying chain map to hide keys of.
    keys: Any
        The keys of the set, if `valid_keys` is not set.
    valid_keys: set | None
        The set of a valid keys.  If None and there are no `keys`, it is assumed that all keys are valid.
    """

    chain_map: ChainMap | ChainMapView
    valid_keys: set

    def __init__(self, mapping: Mapping, *keys: Any, valid_keys: set | None = None):
        # get around the frozen attribute.
        chain_map = mapping if isinstance(mapping, (ChainMap, ChainMapView)) else ChainMap(mapping)
        object.__setattr__(self, "chain_map", chain_map)
        object.__setattr__(
            self, "valid_keys", valid_keys if valid_keys is not None else set(keys) or set(chain_map.keys())
        )

    def __missing__(self, key):
        raise KeyError(key)

    def __getitem__(self, key):
        if key not in self.valid_keys:
            return self.__missing__(key)
        try:
            return self.chain_map[key]
        except KeyError:
            return self.__missing__(key)

    def get(self, key, default=None):
        return self[key] if key in self else default

    def __len__(self):
        return len(list(filter(lambda key: key in self.valid_keys, self.chain_map.keys())))

    def __iter__(self):
        return filter(lambda key: key in self.valid_keys, self.chain_map.keys())

    def __contains__(self, key):
        return key in self.valid_keys and key in self.chain_map

    def __bool__(self):
        return any(self.chain_map[k] for k in self)

    @classmethod
    def fromkeys(cls, iterable, *args):
        """
        Create a ChainMap with a single dict created from the iterable.
        """
        return cls(ChainMap.fromkeys(iterable, *args), iterable)

    def copy(self):
        return self.__class__(self.chain_map, valid_keys=self.valid_keys)

    __copy__ = copy

    def new_child(self, m=None, **kwargs):
        """
        New ChainMap with a new map followed by all previous maps.

        Notes
        -----
        If no map is provided, an empty dict is used.
        Keyword arguments update the map or new empty dict.
        """
        return self.__class__(self.chain_map.new_child(m, **kwargs), valid_keys=self.valid_keys)

    @property
    def parents(self):
        """
        New ChainMap from maps[1:].
        """
        return self.__class__(self.chain_map.parents, valid_keys=self.valid_keys)

    @property
    def maps(self) -> tuple[Mapping]:
        """
        The maps associated with the underlying chain map.

        Returns
        -------
        tuple[Mapping]
            A series of maps that are present in the underlying chain map.

        Notes
        -----
        Does not hide invalid keys, defined from `valid_keys`.
        """
        return self.chain_map.maps


def sequence_to_pretty_str(values: Sequence) -> str:
    """
    Makes a sequence into an English readable string.

    Parameters
    ----------
    values : Sequence
        The sequence to generate a string for.

    Returns
    -------
    str
        The English readable string.
    """
    arguments = len(values)
    if arguments == 0:
        return ""
    if arguments == 1:
        return f"{values[0]!s}"
    if arguments == 2:
        return f"{values[0]!s} and {values[1]!s}"
    return f"{', '.join(str(v) for v in values[: -1])} and {values[-1]}"
