from __future__ import annotations

from collections.abc import Mapping
from reprlib import recursive_repr
from typing import Any, TypeVar

from attr import attrs

_CMV = TypeVar("_CMV", bound="ChainMapView")


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
            try:
                return mapping[key]  # can't use 'key in mapping' with defaultdict
            except KeyError:
                pass
        return self.__missing__(key)  # support subclasses that define __missing__

    def get(self, key, default=None):
        return self[key] if key in self else default

    def __len__(self):
        return len(set().union(*self.maps))  # reuses stored hash values if possible

    def __iter__(self):
        d = {}
        for mapping in reversed(self.maps):
            d.update(dict.fromkeys(mapping))  # reuses stored hash values if possible
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
        if not isinstance(other, Mapping):
            return NotImplemented
        return self.__class__(self, other)

    def __ror__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        return self.__class__(other, self)


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
