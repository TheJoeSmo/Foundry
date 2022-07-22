"""
Credit to Python as I just copied most of their tests and changed them to use pytest.
"""
from collections import OrderedDict, UserDict

from pytest import raises

from foundry.core import ChainMap


class DefaultChainMap(ChainMap):
    def __missing__(self, key):
        return 999


class Subclass(ChainMap):
    pass


class SubclassRor(ChainMap):
    def __ror__(self, other):
        return super().__ror__(other)


def test_chain_map_initialization_empty():
    assert ChainMap().maps == ()


def test_chain_map_initialization_simple():
    assert ChainMap({1: 2}).maps == ({1: 2},)


def test_chain_map_initialization_complex():
    assert ChainMap({1: 2}, {2: 3, 4: 5}).maps == ({1: 2}, {2: 3, 4: 5})


def test_chain_map_new_child_empty_empty():
    assert ChainMap().new_child().maps == ()


def test_chain_map_new_child_simple_empty():
    assert ChainMap({1: 2}).new_child().maps == ({1: 2},)


def test_chain_map_new_child_empty_simple_single():
    assert ChainMap().new_child({3: 4}).maps == ({3: 4},)


def test_chain_map_new_child_empty_simple_kwargs():
    assert ChainMap().new_child(test=3).maps == ({"test": 3},)


def test_chain_map_new_child_simple_simple_single():
    assert ChainMap({1: 2}).new_child({3: 4}).maps == ({3: 4}, {1: 2})


def test_chain_map_new_child_simple_simple_kwargs():
    assert ChainMap({1: 2}).new_child(test=3).maps == ({"test": 3}, {1: 2})


def test_chain_map_new_child_complex_empty():
    assert ChainMap({1: 2}, {2: 3, 4: 5}).new_child().maps == ({1: 2}, {2: 3, 4: 5})


def test_chain_map_new_child_complex_simple_single():
    assert ChainMap({1: 2}, {2: 3, 4: 5}).new_child({6: 7}).maps == ({6: 7}, {1: 2}, {2: 3, 4: 5})


def test_chain_map_new_child_complex_simple_kwargs():
    assert ChainMap({1: 2}, {2: 3, 4: 5}).new_child(test=6).maps == ({"test": 6}, {1: 2}, {2: 3, 4: 5})


def test_chain_map_new_child_simple_complex_single():
    assert ChainMap({1: 2}).new_child({2: 3, 4: 5}).maps == ({2: 3, 4: 5}, {1: 2})


def test_chain_map_new_child_simple_complex_kwargs():
    assert ChainMap({1: 2}).new_child(test=3, test2=4).maps == ({"test": 3, "test2": 4}, {1: 2})


def test_chain_map_items_empty():
    assert ChainMap().items() == {}.items()


def test_chain_map_items_simple():
    assert ChainMap({1: 2, 3: 4}).items() == {1: 2, 3: 4}.items()


def test_chain_map_items_complex():
    assert ChainMap({1: 2}, {1: 0, 3: 4}, {3: 0, 5: 6}).items() == {1: 2, 3: 4, 5: 6}.items()


def test_chain_map_repr_empty():
    repr(ChainMap())


def test_chain_map_repr_simple():
    repr(ChainMap({1: 2}, {1: 0, 3: 4}, {3: 0, 5: 6}))


def test_chain_map_repr_recursive():
    a = {1: 2}
    b = {3: a}
    a[4] = b  # type: ignore
    repr(ChainMap(a))


def test_chain_map_str_empty():
    str(ChainMap())


def test_chain_map_str_simple():
    str(ChainMap({1: 2}, {1: 0, 3: 4}, {3: 0, 5: 6}))


def test_chain_map_str_recursive():
    a = {1: 2}
    b = {3: a}
    a[4] = b  # type: ignore
    str(ChainMap(a))


def test_chain_map_get_item_simple():
    assert DefaultChainMap({1: 2})[1] == 2


def test_chain_map_get_item_complex():
    a = DefaultChainMap({1: 2}, {3: 4, 5: 6}, {1: 0, 3: 0, 5: 0})
    assert a[1] == 2
    assert a[3] == 4
    assert a[5] == 6


def test_chain_map_get_item_missing_empty():
    assert DefaultChainMap()[1] == 999


def test_chain_map_get_item_missing_simple():
    assert DefaultChainMap({1: 2})[3] == 999


def test_chain_map_get_item_missing_complex():
    assert DefaultChainMap({1: 2}, {3: 4, 5: 6})[7] == 999


def test_chain_map_len_empty():
    assert len(ChainMap()) == 0


def test_chain_map_len_simple():
    assert len(ChainMap({1: 2}, {3: 4, 5: 6})) == 3


def test_chain_map_len_complex():
    assert len(ChainMap({}, {1: 2}, {3: 4, 5: 6}, {1: 0, 3: 0, 5: 0})) == 3


def test_chain_map_contains_empty():
    assert 1 not in ChainMap()


def test_chain_map_contains_simple():
    assert 1 in ChainMap({1: 2})


def test_chain_map_contains_complex():
    a = ChainMap({1: 2}, {3: 4, 5: 6}, {1: 0, 3: 0, 5: 0})
    assert 1 in a
    assert 2 not in a
    assert 3 in a
    assert 4 not in a
    assert 5 in a
    assert 6 not in a


def test_chain_map_ordering():
    # Combined order matches a series of dict updates from last to first.
    # This test relies on the ordering of the underlying dicts.

    baseline = {"music": "bach", "art": "rembrandt"}
    adjustments = {"art": "van gogh", "opera": "carmen"}

    cm = ChainMap(adjustments, baseline)

    combined = baseline.copy()
    combined.update(adjustments)

    assert list(combined.items()) == list(cm.items())


def test_chain_map_bool_empty():
    assert not ChainMap()


def test_chain_map_bool_empty_dict():
    assert not ChainMap({})


def test_chain_map_bool_empty_dicts():
    assert not ChainMap({}, {})


def test_chain_map_bool_simple():
    assert ChainMap({1: 2}, {})


def test_chain_map_bool_complex():
    assert ChainMap({}, {1: 2})


def test_chain_map_order_preservation():
    d = ChainMap(
        OrderedDict(j=0, h=88888),
        OrderedDict(),
        OrderedDict(i=9999, d=4444, c=3333),
        OrderedDict(f=666, b=222, g=777, c=333, h=888),
        OrderedDict(),
        OrderedDict(e=55, b=22),
        OrderedDict(a=1, b=2, c=3, d=4, e=5),
        OrderedDict(),
    )
    assert "".join(d) == "abcdefghij"
    assert list(d.items()) == [
        ("a", 1),
        ("b", 222),
        ("c", 3333),
        ("d", 4444),
        ("e", 55),
        ("f", 666),
        ("g", 777),
        ("h", 88888),
        ("i", 9999),
        ("j", 0),
    ]


def test_chain_map_iter_not_calling_getitem_on_maps():
    class DictWithGetItem(UserDict):
        def __init__(self, *args, **kwds):
            self.called = False
            UserDict.__init__(self, *args, **kwds)

        def __getitem__(self, item):
            self.called = True
            UserDict.__getitem__(self, item)

    d = DictWithGetItem(a=1)
    c = ChainMap(d)
    d.called = False

    set(c)  # iterate over chain map
    assert not d.called


def test_chain_map_dict_coercion():
    d = ChainMap(dict(a=1, b=2), dict(b=20, c=30))
    assert dict(d) == dict(a=1, b=2, c=30)
    assert dict(d.items()) == dict(a=1, b=2, c=30)


def test_chain_map_union_simple():
    assert (ChainMap({1: 2, 3: 4}) | ChainMap({5: 6, 7: 8})).maps == (ChainMap({1: 2, 3: 4}), ChainMap({5: 6, 7: 8}))


def test_chain_map_union_copy():
    assert (ChainMap({1: 2, 3: 4}) | ChainMap({1: 2, 3: 4})).maps == (ChainMap({1: 2, 3: 4}), ChainMap({1: 2, 3: 4}))


def test_chain_map_union_invalid():
    with raises(TypeError):
        ChainMap() | [(1, 2), (3, 4)]


def test_chain_map_union_class_subclass():
    a = ChainMap({1: 2, 3: 4}) | Subclass({5: 6, 7: 8})
    assert isinstance(a, ChainMap)
    assert a.maps == (ChainMap({1: 2, 3: 4}), Subclass({5: 6, 7: 8}))


def test_chain_map_union_subclass_class():
    a = Subclass({5: 6, 7: 8}) | ChainMap({1: 2, 3: 4})
    assert isinstance(a, Subclass)
    assert a.maps == (Subclass({5: 6, 7: 8}), ChainMap({1: 2, 3: 4}))


def test_chain_map_union_reverse():
    a = ChainMap({1: 2, 3: 4}) | SubclassRor({5: 6, 7: 8})
    assert isinstance(a, SubclassRor)
    assert a.maps == (ChainMap({1: 2, 3: 4}), SubclassRor({5: 6, 7: 8}))
